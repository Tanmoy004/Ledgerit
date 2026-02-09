import pandas as pd
import re
from img2table.document import PDF
from img2table.ocr import PaddleOCR
import PyPDF2
import io
from dateutil import parser as date_parser

def safe_str(value):
    """Convert any value to string safely - prevents regex errors"""
    if pd.isna(value):
        return ""
    return str(value).strip()

def get_ocr_instance():
    return PaddleOCR(lang="en")

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

def process_jk_pdf(pdf_bytes, filename):
    """Process JK Bank PDF with custom logic"""
    try:
        pdf_doc = PDF(pdf_bytes)
        ocr = get_ocr_instance()
        
        pdf_tables = pdf_doc.extract_tables(
            ocr=ocr,
            implicit_rows=True,
            implicit_columns=True,
            borderless_tables=True,
            min_confidence=50
        )
        
        all_rows = []
        pending_transaction = None
        previous_balance = None
        opening_balance_value = None  # Store B/F separately
        
        for page_num, page_tables in pdf_tables.items():
            for table in page_tables:
                df = table.df
                
                if len(df) < 3:
                    continue
                
                # Check if this page is a summary/footer page
                page_text = " ".join([str(cell) for row in df.iterrows() for cell in row[1] if pd.notna(cell) and str(cell).strip()])
                if any(phrase in page_text.upper() for phrase in ["PAGE TOTAL:", "GRAND TOTAL:", "END OF STATEMENT", "FUNDS IN CLEARING"]):
                    print(f"Skipping summary page {page_num}")
                    continue
                
                for idx, row in df.iterrows():
                    row_text = " ".join([str(cell) for cell in row if pd.notna(cell) and str(cell).strip()])
                    
                    if not row_text.strip():
                        continue
                    
                    # Skip header/footer content and summary lines
                    if any(keyword in row_text.upper() for keyword in ["STATEMENT", "ACCOUNT", "PAGE", "MANAGER", "STAMP", "PROP-YASIR", "KOLKATA MAIN", "UNLESS THE CONSTITUENT", "JAMMU AND KASHMIR BANK", "IFSC CODE", "MICR CODE", "PHONE CODE", "PRINTED BY", "CKYC ID", "GRAND TOTAL", "PAGE TOTAL", "ONAQ FRUIT COMPANY", "FUNDS IN CLEARING", "AVAILABLE AMOUNT", "FFD CONTRIBUTION"]):
                        continue
                    
                    # Check for B/F (opening balance)
                    if "B/F" in row_text.upper():
                        balance_match = re.search(r'([\d,]+\.\d{2}(?:Cr|Dr))', row_text)
                        if balance_match:
                            previous_balance = balance_match.group(1)
                            if opening_balance_value is None:  # Only set once
                                opening_balance_value = previous_balance
                            print(f"Found B/F balance: {previous_balance}")
                        continue
                    
                    date_match = re.search(r'\b(\d{2}-\d{2}-\d{4})\b', row_text)
                    
                    # Stop processing if we hit footer content
                    if any(phrase in row_text.upper() for phrase in ["UNLESS THE CONSTITUENT NOTIFIES", "GRAND TOTAL:", "R.N.MUKHERJI ROAD"]):
                        break
                    
                    if date_match:
                        # Check if this date line contains footer content - skip it
                        if any(phrase in row_text.upper() for phrase in ["UNLESS THE CONSTITUENT", "IMMEDIATELY OF ANY DISCREPANCY", "GRAND TOTAL", "R.N.MUKHERJI ROAD"]):
                            continue
                            
                        if pending_transaction:
                            all_rows.append(pending_transaction)
                        
                        date = date_match.group(1)
                        remaining = row_text[date_match.end():].strip()
                        
                        amount_pattern = r'([\d,]+\.\d{2})\s+([\d,]+\.\d{2}(?:Cr|Dr))'
                        amount_match = re.search(amount_pattern, remaining)
                        
                        if amount_match:
                            amount = amount_match.group(1).replace(',', '')
                            balance = amount_match.group(2)
                            description = remaining[:amount_match.start()].strip()
                            
                            # Compare balances to determine credit/debit
                            current_bal = float(balance.replace('Cr', '').replace('Dr', '').replace(',', ''))
                            prev_bal = float(previous_balance.replace('Cr', '').replace('Dr', '').replace(',', '')) if previous_balance else 0
                            
                            if current_bal > prev_bal:
                                credit = amount
                                debit = ''
                            else:
                                debit = amount
                                credit = ''
                            
                            pending_transaction = {
                                'Date': date,
                                'Description': description,
                                'Debit': debit,
                                'Credit': credit,
                                'Balance': balance
                            }
                            previous_balance = balance
                        else:
                            # Only create transaction if description doesn't contain footer text
                            if not any(phrase in remaining.upper() for phrase in ["IMMEDIATELY OF ANY DISCREPANCY", "UNLESS THE CONSTITUENT", "IT WILL BE TAKEN"]):
                                pending_transaction = {
                                    'Date': date,
                                    'Description': remaining,
                                    'Debit': '',
                                    'Credit': '',
                                    'Balance': ''
                                }
                    else:
                        # Stop processing if we hit footer content in continuation lines
                        if any(phrase in row_text.upper() for phrase in ["UNLESS THE CONSTITUENT", "GRAND TOTAL", "R.N.MUKHERJI ROAD"]):
                            break
                            
                        if pending_transaction:
                            amount_pattern = r'([\d,]+\.\d{2})\s+([\d,]+\.\d{2}(?:Cr|Dr))'
                            amount_match = re.search(amount_pattern, row_text)
                            
                            if amount_match:
                                desc_part = row_text[:amount_match.start()].strip()
                                if desc_part:
                                    pending_transaction['Description'] += " " + desc_part
                                
                                parts = row_text[amount_match.start():].strip().split()
                                amounts = [p for p in parts if re.match(r'[\d,]+\.\d{2}', p)]
                                
                                if len(amounts) >= 2:
                                    amount = amounts[0].replace(',', '')
                                    balance = amounts[1]
                                    
                                    current_bal = float(balance.replace('Cr', '').replace('Dr', '').replace(',', ''))
                                    prev_bal = float(previous_balance.replace('Cr', '').replace('Dr', '').replace(',', '')) if previous_balance else 0
                                    
                                    if current_bal > prev_bal:
                                        pending_transaction['Credit'] = amount
                                        pending_transaction['Debit'] = ''
                                    else:
                                        pending_transaction['Debit'] = amount
                                        pending_transaction['Credit'] = ''
                                    
                                    pending_transaction['Balance'] = balance
                                    previous_balance = balance
                            else:
                                pending_transaction['Description'] += " " + row_text.strip()
        
        if pending_transaction:
            # Only add transaction if it has valid financial data
            if pending_transaction.get('Balance') or pending_transaction.get('Debit') or pending_transaction.get('Credit'):
                all_rows.append(pending_transaction)
        
        if not all_rows:
            return None, None, None, None
        
        final_df = pd.DataFrame(all_rows)
        
        # Convert date columns to datetime type
        final_df = convert_date_columns(final_df)
        
        # Opening balance is the B/F balance we captured
        opening_balance = {'Balance': opening_balance_value} if opening_balance_value else None
        print(f"\nOpening balance (B/F): {opening_balance}")
        
        # Closing balance is the last transaction balance
        closing_balance = None
        if len(final_df) > 0:
            closing_balance = {'Balance': final_df.iloc[-1]['Balance']}
            print(f"Closing balance: {closing_balance}\n")
        
        return final_df, opening_balance, closing_balance, None
        
    except Exception as e:
        print(f"JK Parser error: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None
