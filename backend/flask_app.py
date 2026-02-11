from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from flask_bcrypt import Bcrypt
import io
import pandas as pd
import PyPDF2
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import sys
import importlib
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import routes
from routes.auth_routes import auth_bp
from routes.subscription_routes import subscription_bp
from controllers.auth_controller import check_token_blacklist
from models.user import User

def clean_xml_text(text):
    """Remove invalid XML characters"""
    if not text:
        return ""
    # Convert to string and remove all invalid XML characters
    text = str(text)
    # Remove characters that are invalid in XML
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\uFFFE\uFFFF]', ' ', text)
    # Also remove any other problematic Unicode characters
    cleaned = ''.join(char for char in cleaned if ord(char) < 65534)
    return cleaned.strip()

# Force reload modules
if 'ifsc_detector' in sys.modules:
    importlib.reload(sys.modules['ifsc_detector'])
if 'bankDetector' in sys.modules:
    importlib.reload(sys.modules['bankDetector'])
if 'bordered' in sys.modules:
    importlib.reload(sys.modules['bordered'])

from bankDetector import detect_bank_from_pdf, classify_bank_type, process_bordered_pdf, process_borderless_pdf, decrypt_pdf_bytes

try:
    from jk_parser import process_jk_pdf
except ImportError:
    def process_jk_pdf(pdf_bytes, filename):
        return None, None, None, None

try:
    from indian_parser import process_indian_pdf
except ImportError:
    def process_indian_pdf(pdf_bytes, filename):
        return None, None, None, None

try:
    from canara_parser import process_canara_pdf
except ImportError:
    def process_canara_pdf(pdf_bytes, filename):
        return None, None, None, None

app = Flask(__name__)
CORS(app)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

# JWT token blacklist check
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return check_token_blacklist(jwt_header, jwt_payload)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(subscription_bp)

@app.route('/')
def home():
    return jsonify({'message': 'Bank Statement API is running'})

@app.route('/test')
def test():
    return jsonify({'status': 'API is working'})

def parse_transactions(df):
    if df is None or df.empty:
        return [], []
    
    # Get original column names from DataFrame
    column_names = df.columns.tolist()
    
    # If columns are numeric (0,1,2...), check if first row has actual headers
    if all(isinstance(col, (int, float)) or str(col).isdigit() for col in column_names):
        first_row = df.iloc[0].fillna("").astype(str).str.strip().tolist()
        # If first row contains banking terms, use as headers
        if any(word in str(cell).lower() for cell in first_row for word in ['date', 'description', 'debit', 'credit', 'balance', 'amount', 'particulars', 'narration']):
            column_names = first_row
            df = df.iloc[1:].reset_index(drop=True)
    
    # Convert cheque/reference columns to string to preserve '-' and other characters
    for col in df.columns:
        col_str = str(col).lower()
        if any(keyword in col_str for keyword in ['cheque', 'chq', 'ref', 'reference', 'instrument']):
            df[col] = df[col].astype(str)
    
    # Format datetime columns to date-only strings
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d')
    
    # Convert to array format preserving order
    transactions = []
    for _, row in df.iterrows():
        row_data = []
        for i in range(len(df.columns)):
            value = str(row.iloc[i]).strip() if pd.notna(row.iloc[i]) else ""
            row_data.append(value)
        transactions.append(row_data)
    
    # Convert column names to strings
    column_names = [str(col) for col in column_names]
    
    return transactions, column_names

@app.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    try:
        user_id = get_jwt_identity()
        
        # Check subscription status first
        if not User.check_subscription_status(user_id):
            return jsonify({
                'error': 'Subscription expired or page limit reached',
                'redirect': '/subscription'
            }), 403
            
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        password = request.form.get('password', '')
        
        pdf_bytes = file.read()
        
        # Handle password protection and count pages after decryption
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            if reader.is_encrypted:
                # Try empty password first (some PDFs report as encrypted but don't need password)
                if reader.decrypt('') == 0:  # Empty password failed
                    if not password:
                        return jsonify({'error': 'PDF is password protected'}), 401
                    
                    decrypted_bytes = decrypt_pdf_bytes(pdf_bytes, password)
                    if decrypted_bytes is None:
                        return jsonify({'error': 'Wrong password'}), 401
                    pdf_bytes = decrypted_bytes
                    
                    # Count pages after successful decryption
                    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            
            page_count = len(reader.pages)
        except UnicodeDecodeError:
            return jsonify({'error': 'PDF file is corrupted or has encoding issues'}), 400
        except Exception as e:
            return jsonify({'error': f'Invalid PDF file: {str(e)}'}), 400
        
        # Validate bank statement BEFORE updating page count
        bank_name = detect_bank_from_pdf(pdf_bytes)
        if not bank_name:
            return jsonify({'error': 'Could not detect bank name. Please upload a valid bank statement.'}), 400
        
        bank_type, standardized_name = classify_bank_type(bank_name)
        print(f"\nDEBUG: bank_type={bank_type}, standardized_name={standardized_name}")
        
        if not bank_type:
            bank_type = "bordered"
        
        # Process bank statement based on type
        if bank_type in ["jk_bank", "indian_bank", "canara_bank"]:
            if bank_type == "jk_bank":
                print(f">>> {standardized_name} detected, using JK parser <<<")
                df, opening_balance, closing_balance, transaction_total = process_jk_pdf(pdf_bytes, file.filename)
            elif bank_type == "indian_bank":
                print(f">>> {standardized_name} detected, using Indian Bank parser <<<")
                df, opening_balance, closing_balance, transaction_total = process_indian_pdf(pdf_bytes, file.filename)
            else:
                print(f">>> {standardized_name} detected, using Canara Bank parser <<<")
                df, opening_balance, closing_balance, transaction_total = process_canara_pdf(pdf_bytes, file.filename)
        elif bank_type == "bordered":
            print(">>> Calling process_bordered_pdf <<<")
            df, opening_balance, closing_balance, transaction_total = process_bordered_pdf(pdf_bytes, file.filename)
        else:
            print(">>> Calling process_borderless_pdf <<<")
            df, opening_balance, closing_balance, transaction_total = process_borderless_pdf(pdf_bytes, file.filename)
        
        # Validate that transactions were found
        if df is None or df.empty:
            return jsonify({'error': 'No transactions found in the PDF. Please ensure this is a valid bank statement with transaction tables.'}), 400
        
        # Only update page count AFTER successful validation and processing
        User.update_pages_used(user_id, page_count)
        
        print("\n" + "="*80)
        print(f"Uploaded: {file.filename}")
        print(f"Bank: {bank_name} | Type: {bank_type}")
        print("="*80)
        print(df)
        print("="*80 + "\n")
        
        transactions, column_names = parse_transactions(df)
        
        # Get updated user stats
        user_stats = User.get_user_stats(user_id)
        
        # Extract opening and closing balance values
        opening_bal_value = None
        closing_bal_value = None
        
        if opening_balance and 'Balance' in opening_balance:
            opening_bal_value = opening_balance['Balance']
            print(f"[DEBUG] Backend opening balance: {opening_bal_value}")
        else:
            print("[DEBUG] No opening balance from backend")
        
        if closing_balance and 'Balance' in closing_balance:
            closing_bal_value = closing_balance['Balance']
            print(f"[DEBUG] Backend closing balance: {closing_bal_value}")
        else:
            print("[DEBUG] No closing balance from backend")
        
        return jsonify({
            'transactions': transactions,
            'columns': column_names,
            'metadata': {
                'bank_name': bank_name,
                'bank_type': bank_type,
                'total_transactions': len(transactions),
                'opening_balance': opening_bal_value,
                'closing_balance': closing_bal_value,
                'pages_processed': page_count
            },
            'user_stats': user_stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/csv', methods=['POST'])
def export_csv():
    try:
        data = request.json
        transactions = data.get('transactions', [])
        df = pd.DataFrame(transactions)
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name=f'transactions_{datetime.now().strftime("%Y%m%d")}.csv')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/tally', methods=['POST'])
def export_tally():
    try:
        data = request.json
        transactions = data.get('transactions', [])
        bank_ledger = data.get('bankLedger', 'Bank Account')
        
        # Clean bank ledger name
        bank_ledger = clean_xml_text(bank_ledger)
        
        root = ET.Element("ENVELOPE")
        header = ET.SubElement(root, "HEADER")
        ET.SubElement(header, "TALLYREQUEST").text = "Import Data"
        
        body = ET.SubElement(root, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        request_desc = ET.SubElement(import_data, "REQUESTDESC")
        ET.SubElement(request_desc, "REPORTNAME").text = "Vouchers"
        
        request_data = ET.SubElement(import_data, "REQUESTDATA")
        
        for i, txn in enumerate(transactions):
            # Clean all transaction data
            clean_txn = {}
            for key, value in txn.items():
                clean_txn[key] = clean_xml_text(value)
            
            voucher = ET.SubElement(request_data, "TALLYMESSAGE", {"UDF:VOUCHERNUMBER": str(i+1)})
            voucher_elem = ET.SubElement(voucher, "VOUCHER", {"REMOTEID": str(i+1), "VCHTYPE": "Journal", "ACTION": "Create"})
            
            ET.SubElement(voucher_elem, "DATE").text = clean_txn.get('date', '')
            ET.SubElement(voucher_elem, "NARRATION").text = clean_txn.get('description', '')
            
            all_ledger_entries = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
            
            ledger_entry1 = ET.SubElement(all_ledger_entries, "LEDGERENTRIES.LIST")
            ET.SubElement(ledger_entry1, "LEDGERNAME").text = bank_ledger
            amount = clean_txn.get('credit', 0) - clean_txn.get('debit', 0)
            ET.SubElement(ledger_entry1, "AMOUNT").text = clean_xml_text(str(amount))
        
        # Generate XML with proper encoding and character handling
        xml_str = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        # Additional cleaning of the entire XML string
        xml_str = re.sub(rb'[\x00-\x08\x0B\x0C\x0E-\x1F\uFFFE\uFFFF]', b' ', xml_str)
        
        output = io.BytesIO(xml_str)
        return send_file(output, mimetype='application/xml', as_attachment=True, download_name=f'tally_{bank_ledger}_{datetime.now().strftime("%Y%m%d")}.xml')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/tdl', methods=['GET'])
def download_tdl():
    try:
        import zipfile
        import tempfile
        
        # Create temporary zip file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
            # Add TDL file
            zip_file.write('tdl/Ledgerit.tdl', 'Ledgerit.tdl')
            # Add README
            zip_file.write('tdl/README.txt', 'Installation_Guide.txt')
        
        return send_file(
            temp_zip.name,
            mimetype='application/zip',
            as_attachment=True,
            download_name='Ledgerit_TDL.zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)