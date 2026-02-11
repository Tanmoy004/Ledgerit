import PyPDF2
import io
import re
import fitz  # PyMuPDF
from PIL import Image
import numpy as np
import cv2
import os
from pathlib import Path
import pandas as pd
from img2table.document import PDF
from img2table.ocr import PaddleOCR
from dateutil import parser as date_parser
from ifsc_detector import extract_ifsc_from_text, get_bank_from_ifsc

def safe_str(value):
    """Convert any value to string safely - prevents regex errors"""
    if pd.isna(value):
        return ""
    return str(value).strip()

def calculate_opening_balance_universal(final_df, is_reverse_chrono):
    """Universal opening balance calculation for all bank formats"""
    if len(final_df) == 0:
        return None
    
    print(f"[DEBUG] All columns: {final_df.columns.tolist()}")
    
    target_row = final_df.iloc[0] if not is_reverse_chrono else final_df.iloc[-1]
    balance_col = debit_col = credit_col = amount_col = dr_cr_col = None
    
    for col in final_df.columns:
        col_lower = str(col).lower().replace(' ', '')
        if 'balance' in col_lower:
            balance_col = col
        elif 'dr' in col_lower and 'cr' in col_lower:
            dr_cr_col = col
        elif 'amount' in col_lower:
            amount_col = col
        elif any(word in col_lower for word in ['debit', 'withdrawal', 'withdraw']):
            debit_col = col
        elif any(word in col_lower for word in ['credit', 'deposit']):
            credit_col = col
    
    print(f"[DEBUG] Found: balance={balance_col}, debit={debit_col}, credit={credit_col}, amount={amount_col}, dr_cr={dr_cr_col}")
    
    # Handle single amount column with DR/CR indicator
    if balance_col and amount_col and dr_cr_col:
        try:
            balance_val = float(str(target_row[balance_col]).replace('INR', '').replace(',', '').strip())
            amount_str = str(target_row[amount_col]).replace('INR', '').replace(',', '').strip()
            dr_cr = str(target_row[dr_cr_col]).strip().upper()
            
            amount_val = float(amount_str) if amount_str and amount_str not in ['', '-', '0.00'] else 0.0
            
            if is_reverse_chrono:
                opening = balance_val + amount_val if dr_cr == 'DR' else balance_val - amount_val
            else:
                # Chronological: DR = add back, CR = subtract
                opening = balance_val + amount_val if dr_cr == 'DR' else balance_val - amount_val
            
            return {'Balance': f'{opening:.2f}', 'Source': 'Calculated'}
        except Exception as e:
            print(f"[ERROR] Opening calc failed: {e}")
    
    # Handle separate debit/credit columns
    if balance_col and debit_col and credit_col:
        try:
            balance_val = float(str(target_row[balance_col]).replace('INR', '').replace(',', '').strip())
            debit_str = str(target_row[debit_col]).replace('INR', '').replace(',', '').strip()
            credit_str = str(target_row[credit_col]).replace('INR', '').replace(',', '').strip()
            debit_val = float(debit_str) if debit_str and debit_str not in ['', '-', '0.00'] else 0.0
            credit_val = float(credit_str) if credit_str and credit_str not in ['', '-', '0.00'] else 0.0
            
            if is_reverse_chrono:
                opening = balance_val + debit_val - credit_val
            else:
                # Chronological: add back debit, subtract credit
                opening = balance_val + debit_val - credit_val
            
            return {'Balance': f'{opening:.2f}', 'Source': 'Calculated'}
        except Exception as e:
            print(f"[ERROR] Opening calc failed: {e}")
    
    return None

def convert_date_columns(df):
    """Convert date columns to datetime type"""
    if df is None or df.empty:
        return df
    
    date_pattern = re.compile(r'date', re.IGNORECASE)
    
    for col in df.columns:
        col_str = str(col).lower()
        if date_pattern.search(col_str):
            try:
                df[col] = df[col].apply(lambda x: 
                    date_parser.parse(re.sub(r'\s+', ' ', str(x)).strip(), fuzzy=True, dayfirst=True) 
                    if pd.notna(x) and str(x).strip() not in ['', '-', 'nan'] 
                    else pd.NaT
                )
                print(f"[DATE] Converted column '{col}' to datetime")
            except Exception as e:
                print(f"[DATE] Failed to convert column '{col}': {e}")
    
    return df

# Bank classification lists
BORDERED_BANKS = [
    "Union Bank of India", "Central Bank of India", "State Bank of India", 
    "Axis Bank", "Yes Bank", "Federal Bank", "ICICI Bank", "IDBI Bank", 
    "Bandhan Bank", "Punjab National Bank", "Indian Overseas Bank"
]

BORDERLESS_BANKS = [
    "Kotak Bank", "IndusInd Bank", "HDFC Bank", "UCO Bank"
]

BANK_NAME_REGEX = re.compile(
    r'(?i)\b([A-Za-z\s&]+(?:bank|financial|credit\s+union|cooperative|society)(?:\s+(?:ltd|limited|inc|corporation|corp))?)\b',
    re.MULTILINE
)

# Cache OCR Instance
_ocr_instance = None

def get_ocr_instance():
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = PaddleOCR(lang="en")
    return _ocr_instance

def decrypt_pdf_bytes(pdf_bytes, password):
    """Decrypt password-protected PDF with multiple methods"""
    # Method 1: Try PyMuPDF first (better encryption support)
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if doc.needs_pass:
            if doc.authenticate(password):
                # Convert back to bytes
                output_bytes = doc.tobytes()
                doc.close()
                return output_bytes
            doc.close()
    except Exception as e:
        print(f"PyMuPDF decryption failed: {e}")
    
    # Method 2: Try PyPDF2 with multiple password variations
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        writer = PyPDF2.PdfWriter()
        
        # Try different password encodings
        passwords_to_try = [
            password,
            password.strip(),
            password.upper(),
            password.lower()
        ]
        
        decryption_successful = False
        for pwd in passwords_to_try:
            try:
                result = reader.decrypt(pwd)
                if result > 0:  # Success
                    decryption_successful = True
                    break
            except Exception:
                continue
        
        if not decryption_successful:
            return None
        
        for page in reader.pages:
            writer.add_page(page)
        
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception as e:
        print(f"PyPDF2 decryption failed: {e}")
        return None

def load_reference_logos():
    """Load reference logos from logos folder"""
    logos_folder = Path('logos')
    reference_logos = {}
    
    if not logos_folder.exists():
        return reference_logos
    
    for logo_file in logos_folder.glob('*'):
        if logo_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.jfif']:
            try:
                logo_image = cv2.imread(str(logo_file))
                if logo_image is not None:
                    bank_name = logo_file.stem
                    reference_logos[bank_name] = logo_image
            except Exception:
                continue
    
    return reference_logos

def extract_logos_from_pdf_top_quarter(pdf_bytes):
    """Extract images only from top 25% of first page"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[0]
        
        # Get page dimensions
        page_rect = page.rect
        page_height = page_rect.height
        
        # Define top 25% area
        top_quarter_rect = fitz.Rect(0, 0, page_rect.width, page_height * 0.25)
        
        logos = []
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            try:
                # Get image position
                img_rect = page.get_image_rects(img[0])[0] if page.get_image_rects(img[0]) else None
                
                # Only process images in top 25%
                if img_rect and img_rect.intersects(top_quarter_rect):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
                    logo = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                    
                    if logo is not None:
                        logos.append(logo)
            except Exception:
                continue
                
        doc.close()
        return logos
        
    except Exception:
        return []

def match_logo_with_references(extracted_logo, reference_logos):
    """Match extracted logo with reference logos - optimized"""
    best_match = None
    best_score = 0
    
    if len(extracted_logo.shape) == 3:
        extracted_gray = cv2.cvtColor(extracted_logo, cv2.COLOR_BGR2GRAY)
    else:
        extracted_gray = extracted_logo
    
    for bank_name, ref_logo in reference_logos.items():
        try:
            if len(ref_logo.shape) == 3:
                ref_gray = cv2.cvtColor(ref_logo, cv2.COLOR_BGR2GRAY)
            else:
                ref_gray = ref_logo
            
            h, w = ref_gray.shape
            # Optimize: Resize to smaller size for faster processing
            max_size = 200
            if w > max_size or h > max_size:
                scale = min(max_size/w, max_size/h)
                new_w, new_h = int(w*scale), int(h*scale)
                ref_gray = cv2.resize(ref_gray, (new_w, new_h))
                extracted_resized = cv2.resize(extracted_gray, (new_w, new_h))
            else:
                extracted_resized = cv2.resize(extracted_gray, (w, h))
            
            result = cv2.matchTemplate(extracted_resized, ref_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            if max_val > best_score:
                best_score = max_val
                best_match = bank_name
                
        except Exception:
            continue
    
    if best_score > 0.6:
        return best_match
    
    return None

def extract_text_from_top_quarter(pdf_bytes):
    """Extract text only from top 25% of first page"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[0]
        
        # Get page dimensions
        page_rect = page.rect
        page_height = page_rect.height
        
        # Define top 25% area
        top_quarter_rect = fitz.Rect(0, 0, page_rect.width, page_height * 0.25)
        
        # Extract text only from top quarter
        text = page.get_text(clip=top_quarter_rect)
        
        doc.close()
        return text
        
    except Exception:
        # Fallback to PyPDF2 method
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            first_page = reader.pages[0]
            full_text = first_page.extract_text()
            
            # Use first 25% of lines as approximation
            lines = full_text.split('\n')
            first_quarter_lines = lines[:len(lines)//4] if len(lines) > 4 else lines
            return '\n'.join(first_quarter_lines)
        except Exception:
            return ""

def extract_bank_name_from_text(text):
    """Extract bank name from text using regex"""
    matches = BANK_NAME_REGEX.findall(text)
    
    if matches:
        # Prioritize matches containing specific bank names
        priority_banks = ['axis', 'hdfc', 'icici', 'kotak', 'indusind', 'yes', 'federal']
        
        for match in matches:
            match_lower = match.lower().strip()
            # Check if this match contains a priority bank name
            for priority in priority_banks:
                if priority in match_lower and 'bank' in match_lower:
                    return match.strip()
        
        # Find the match that contains actual bank name, not generic terms
        for match in matches:
            match_lower = match.lower().strip()
            if not match_lower.startswith(('account', 'statement', 'report')) and len(match_lower) > 5:
                return match.strip()
        
        # If no specific bank name found, return the longest match
        longest_match = max(matches, key=len)
        return longest_match.strip()
    
    return None

def extract_balances_from_pdf(pdf_bytes):
    """Universal balance extraction - works for ANY bank"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        
        opening_balance = None
        closing_balance = None
        
        opening_patterns = [
            r'Opening\s+Balance[:\s]+(?:INR|₹|Rs\.?|USD|\$)?\\s*([0-9,]+\.\\d{2})\s*(Cr|Dr)?',
            r'Opening\s+Bal\.?[:\s]+(?:INR|₹|Rs\.?|USD|\$)?\s*([0-9,]+\.\\d{2})\s*(Cr|Dr)?',
            r'B/?F[:\s]+(?:INR|₹|Rs\.?|USD|\$)?\s*([0-9,]+\.\\d{2})\s*(Cr|Dr)?',
        ]
        
        for pattern in opening_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                balance_val = match.group(1).replace(',', '')
                cr_dr = match.group(2) if len(match.groups()) > 1 and match.group(2) else ''
                opening_balance = {'Balance': balance_val + cr_dr, 'Source': 'PDF'}
                print(f"[EXTRACT] Opening Balance found: {opening_balance}")
                break
        
        # Disable closing balance PDF extraction - table data is more accurate
        
        return opening_balance, closing_balance
    except Exception as e:
        print(f"[EXTRACT] Balance extraction error: {e}")
        return None, None

def detect_bank_from_pdf(pdf_bytes):
    """Main function to detect bank name - IFSC first, then text, then logo"""
    try:
        # Method 1: IFSC code detection (most reliable)
        text = extract_text_from_top_quarter(pdf_bytes)
        if text.strip():
            ifsc_code = extract_ifsc_from_text(text)
            if ifsc_code:
                bank_name = get_bank_from_ifsc(ifsc_code)
                if bank_name:
                    print(f"[IFSC] Detected: {bank_name} (IFSC: {ifsc_code})")
                    return bank_name
        
        # Method 2: Text-based bank name extraction
        if text.strip():
            bank_name = extract_bank_name_from_text(text)
            if bank_name:
                return bank_name
            
        # Method 3: Logo detection as fallback
        reference_logos = load_reference_logos()
        if reference_logos:
            extracted_logos = extract_logos_from_pdf_top_quarter(pdf_bytes)
            for logo in extracted_logos[:2]:
                bank_name = match_logo_with_references(logo, reference_logos)
                if bank_name:
                    return bank_name.replace('_', ' ')
        
        return None
        
    except Exception as e:
        print(f"Detection error: {e}")
        return None

def classify_bank_type(bank_name):
    """Classify bank into bordered or borderless category using regex matching"""
    if not bank_name:
        return None, None
    
    bank_name_lower = bank_name.lower().strip()
    
    # Check for Jammu and Kashmir Bank
    if re.search(r'jammu.*kashmir.*bank', bank_name_lower):
        return "jk_bank", "Jammu and Kashmir Bank"
    
    # Check for Indian Bank
    if re.search(r'indian.*bank', bank_name_lower):
        return "indian_bank", "INDIAN BANK"
    
    # Check for Canara Bank
    if re.search(r'canara.*bank', bank_name_lower):
        return "canara_bank", "CANARA BANK"
    
    # Check bordered banks with regex matching - prioritize specific matches
    if re.search(r'axis.*bank', bank_name_lower):
        return "bordered", "Axis Bank"
    elif re.search(r'icici.*bank', bank_name_lower):
        return "bordered", "ICICI Bank"
    elif re.search(r'yes.*bank', bank_name_lower):
        return "bordered", "Yes Bank"
    elif re.search(r'(state.*bank|sbi)', bank_name_lower):
        return "bordered", "State Bank of India"
    elif re.search(r'union.*bank', bank_name_lower):
        return "bordered", "Union Bank of India"
    elif re.search(r'central.*bank', bank_name_lower):
        return "bordered", "Central Bank of India"
    elif re.search(r'federal.*bank', bank_name_lower):
        return "bordered", "Federal Bank"
    elif re.search(r'idbi.*bank', bank_name_lower):
        return "bordered", "IDBI Bank"
    elif re.search(r'bandhan.*bank', bank_name_lower):
        return "bordered", "Bandhan Bank"
    elif re.search(r'punjab.*national.*bank', bank_name_lower):
        return "bordered", "Punjab National Bank"
    elif re.search(r'indian.*overseas.*bank', bank_name_lower):
        return "bordered", "Indian Overseas Bank"
    
    # Check borderless banks with regex matching
    elif re.search(r'kotak.*bank', bank_name_lower):
        return "borderless", "Kotak Bank"
    elif re.search(r'indusind.*bank', bank_name_lower):
        return "borderless", "IndusInd Bank"
    elif re.search(r'hdfc.*bank', bank_name_lower):
        return "borderless", "HDFC Bank"
    elif re.search(r'uco.*bank', bank_name_lower):
        return "borderless", "UCO Bank"
    
    return None, None

# Import processing functions from bordered and borderless modules
from bordered import (
    has_header_in_first_row as bordered_has_header_in_first_row,
    has_transaction_in_first_row as bordered_has_transaction_in_first_row,
    process_header_and_duplicates as bordered_process_header_and_duplicates,
    extract_opening_balance as bordered_extract_opening_balance,
    extract_closing_balance as bordered_extract_closing_balance,
    extract_transaction_total as bordered_extract_transaction_total,
    merge_multiline_transactions as bordered_merge_multiline_transactions,
    clean_extra_spaces as bordered_clean_extra_spaces,
    CHEQUE_NUMBER_REGEX
)

from borderless import (
    has_header_in_first_row as borderless_has_header_in_first_row,
    has_transaction_in_first_row as borderless_has_transaction_in_first_row,
    has_excluded_headers_in_first_row,
    is_continuation_table,
    process_header_and_duplicates as borderless_process_header_and_duplicates,
    extract_opening_balance as borderless_extract_opening_balance,
    extract_closing_balance as borderless_extract_closing_balance,
    extract_transaction_total as borderless_extract_transaction_total,
    merge_multiline_transactions as borderless_merge_multiline_transactions,
    clean_extra_spaces as borderless_clean_extra_spaces
)

# Import JK Bank parser
try:
    from jk_parser import process_jk_pdf
except ImportError:
    def process_jk_pdf(pdf_bytes, filename):
        return None, None, None, None

# Import Indian Bank parser
try:
    from indian_parser import process_indian_pdf
except ImportError:
    def process_indian_pdf(pdf_bytes, filename):
        return None, None, None, None

# Import Canara Bank parser
try:
    from canara_parser import process_canara_pdf
except ImportError:
    def process_canara_pdf(pdf_bytes, filename):
        return None, None, None, None

def calculate_opening_from_first_transaction(df):
    """Calculate opening balance from first transaction"""
    if df.empty:
        return None
    
    last_row = df.iloc[-1]
    balance_col = debit_col = credit_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'balance' in col_lower:
            balance_col = col
        elif 'debit' in col_lower or 'withdrawal' in col_lower:
            debit_col = col
        elif 'credit' in col_lower or 'deposit' in col_lower:
            credit_col = col
    
    if balance_col:
        try:
            balance = str(last_row[balance_col]).replace(',', '').strip()
            debit = str(last_row[debit_col]).replace(',', '').strip() if debit_col else '0'
            credit = str(last_row[credit_col]).replace(',', '').strip() if credit_col else '0'
            
            balance_val = float(re.sub(r'[^0-9.]', '', balance)) if balance else 0
            debit_val = float(re.sub(r'[^0-9.]', '', debit)) if debit and debit != '-' else 0
            credit_val = float(re.sub(r'[^0-9.]', '', credit)) if credit and credit != '-' else 0
            
            opening = balance_val + debit_val - credit_val
            if opening > 0:
                return {'Balance': f'{opening:.2f}', 'Source': 'Calculated'}
        except:
            pass
    
    return None

def process_bordered_pdf(pdf_bytes, filename):
    """Process PDF using bordered table logic - optimized"""
    pdf_opening_balance, pdf_closing_balance = extract_balances_from_pdf(pdf_bytes)
    
    pdf_doc = PDF(pdf_bytes)
    ocr = get_ocr_instance()
    
    pdf_tables = pdf_doc.extract_tables(
        ocr=ocr,
        implicit_rows=False,
        implicit_columns=False,
        borderless_tables=False,
        min_confidence=50
    )
    
    all_pages = []
    cheque_column_index = None
    first_table_columns = None
    
    print(f"[DEBUG] Total tables found: {sum(len(tables) for tables in pdf_tables.values())}")
    
    for page_num, page_tables in pdf_tables.items():
        for table in page_tables:
            df = table.df
            print(f"[DEBUG] Page {page_num}, Table rows: {len(df)}, Has header: {bordered_has_header_in_first_row(df)}, Has transaction: {bordered_has_transaction_in_first_row(df)}")
            if bordered_has_header_in_first_row(df) or bordered_has_transaction_in_first_row(df):
                if not all_pages:
                    if bordered_has_header_in_first_row(df):
                        header_row = df.iloc[0].fillna("").astype(str).str.strip().tolist()
                    else:
                        header_row = df.columns.tolist()
                    
                    for i, col in enumerate(header_row):
                        if CHEQUE_NUMBER_REGEX.search(col):
                            cheque_column_index = i
                            break
                    
                    first_table_columns = len(df.columns)
                    all_pages.append(df)
                else:
                    current_columns = len(df.columns)
                    if current_columns == first_table_columns - 1 and cheque_column_index is not None:
                        df_list = df.values.tolist()
                        for row in df_list:
                            row.insert(cheque_column_index, "")
                        
                        new_columns = list(range(first_table_columns))
                        df = pd.DataFrame(df_list, columns=new_columns)
                    
                    all_pages.append(df)
    
    if not all_pages:
        return None, None, None, None
    
    final_df = pd.concat(all_pages, ignore_index=True)
    final_df = final_df.fillna("")
    
    final_df = bordered_process_header_and_duplicates(final_df)
    final_df, opening_balance = bordered_extract_opening_balance(final_df)
    final_df, closing_balance = bordered_extract_closing_balance(final_df)
    final_df, transaction_total = bordered_extract_transaction_total(final_df)
    
    print(f"[DEBUG] Rows before merge: {len(final_df)}")
    final_df = bordered_merge_multiline_transactions(final_df)
    print(f"[DEBUG] Rows after merge: {len(final_df)}")
    
    final_df = bordered_clean_extra_spaces(final_df)
    final_df = final_df.replace(r'[^\x00-\x7F]+', '-', regex=True)
    
    # Detect order BEFORE opening balance calculation
    is_reverse_chrono = False
    if len(final_df) >= 2:
        date_col = None
        for col in final_df.columns:
            if 'date' in str(col).lower() and 'value' not in str(col).lower():
                date_col = col
                break
        
        if date_col:
            try:
                first_date = date_parser.parse(str(final_df.iloc[0][date_col]), fuzzy=True, dayfirst=True)
                last_date = date_parser.parse(str(final_df.iloc[-1][date_col]), fuzzy=True, dayfirst=True)
                is_reverse_chrono = first_date > last_date
                print(f"[ORDER] Reverse chronological: {is_reverse_chrono}")
            except Exception as e:
                print(f"[ORDER] Failed: {e}")
    
    if not opening_balance:
        opening_balance = pdf_opening_balance
    
    if not opening_balance:
        opening_balance = calculate_opening_balance_universal(final_df, is_reverse_chrono)
        if opening_balance:
            print(f"[FALLBACK] Opening Balance: {opening_balance}")
    
    print(f"\n=== FINAL OPENING BALANCE: {opening_balance} ===")
    
    if len(final_df) > 0:
        target_row = final_df.iloc[0] if is_reverse_chrono else final_df.iloc[-1]
        for col in final_df.columns:
            if 'balance' in str(col).lower():
                balance_str = str(target_row[col]).replace('INR', '').replace(',', '').strip()
                if balance_str and balance_str not in ['', '-', 'nan']:
                    closing_balance = {'Balance': balance_str, 'Source': 'Table'}
                    print(f"[TABLE] Closing Balance: {closing_balance}")
                    break
    
    print(f"=== FINAL CLOSING BALANCE: {closing_balance} ===\n")
    
    final_df = convert_date_columns(final_df)
    
    return final_df, opening_balance, closing_balance, transaction_total

def process_borderless_pdf(pdf_bytes, filename):
    """Process PDF using borderless table logic - optimized"""
    pdf_opening_balance, pdf_closing_balance = extract_balances_from_pdf(pdf_bytes)
    
    pdf_doc = PDF(pdf_bytes)
    ocr = get_ocr_instance()
    
    pdf_tables = pdf_doc.extract_tables(
        ocr=ocr,
        implicit_rows=True,
        implicit_columns=True,
        borderless_tables=True,
        min_confidence=50
    )
    
    all_pages = []
    expected_columns = None
    
    for page_num, page_tables in pdf_tables.items():
        for table in page_tables:
            df = table.df
            
            if borderless_has_header_in_first_row(df) or borderless_has_transaction_in_first_row(df):
                if not has_excluded_headers_in_first_row(df):
                    if expected_columns is None:
                        expected_columns = len(df.columns)
                    all_pages.append(df)
            elif is_continuation_table(df, expected_columns):
                all_pages.append(df)
    
    if not all_pages:
        return None, None, None, None
    
    final_df = pd.concat(all_pages, ignore_index=True)
    final_df = final_df.fillna("")
    
    final_df = borderless_process_header_and_duplicates(final_df)
    final_df, opening_balance = borderless_extract_opening_balance(final_df)
    final_df, closing_balance = borderless_extract_closing_balance(final_df)
    final_df, transaction_total = borderless_extract_transaction_total(final_df)
    final_df = borderless_merge_multiline_transactions(final_df)
    final_df = borderless_clean_extra_spaces(final_df)
    final_df = final_df.replace('', '-')
    final_df = final_df.replace(r'[^\x00-\x7F]+', '-', regex=True)
    
    # Detect order BEFORE opening balance calculation
    is_reverse_chrono = False
    if len(final_df) >= 2:
        date_col = None
        for col in final_df.columns:
            if 'date' in str(col).lower() and 'value' not in str(col).lower():
                date_col = col
                break
        
        if date_col:
            try:
                first_date = date_parser.parse(str(final_df.iloc[0][date_col]), fuzzy=True, dayfirst=True)
                last_date = date_parser.parse(str(final_df.iloc[-1][date_col]), fuzzy=True, dayfirst=True)
                is_reverse_chrono = first_date > last_date
                print(f"[ORDER] Reverse chronological: {is_reverse_chrono}")
            except Exception as e:
                print(f"[ORDER] Failed: {e}")
    
    if not opening_balance:
        opening_balance = pdf_opening_balance
    
    if not opening_balance:
        opening_balance = calculate_opening_balance_universal(final_df, is_reverse_chrono)
        if opening_balance:
            print(f"[FALLBACK] Opening Balance: {opening_balance}")
    
    print(f"\n=== FINAL OPENING BALANCE: {opening_balance} ===")
    
    if len(final_df) > 0:
        target_row = final_df.iloc[0] if is_reverse_chrono else final_df.iloc[-1]
        for col in final_df.columns:
            if 'balance' in str(col).lower():
                balance_str = str(target_row[col]).replace('INR', '').replace(',', '').strip()
                if balance_str and balance_str not in ['', '-', 'nan']:
                    closing_balance = {'Balance': balance_str, 'Source': 'Table'}
                    print(f"[TABLE] Closing Balance: {closing_balance}")
                    break
    
    print(f"=== FINAL CLOSING BALANCE: {closing_balance} ===\n")
    
    final_df = convert_date_columns(final_df)
    
    return final_df, opening_balance, closing_balance, transaction_total
