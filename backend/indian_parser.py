import pandas as pd
import re
from img2table.document import PDF
from img2table.ocr import PaddleOCR
from dateutil import parser as date_parser

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

def process_indian_pdf(pdf_bytes, filename):
    """Process Indian Bank PDF with custom logic"""
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
        opening_balance_value = None
        
        for page_num, page_tables in pdf_tables.items():
            for table in page_tables:
                df = table.df
                
                if len(df) < 2:
                    continue
                
                for idx, row in df.iterrows():
                    row_text = " ".join([str(cell) for cell in row if pd.notna(cell) and str(cell).strip()])
                    
                    if not row_text.strip():
                        continue
                    
                    # Skip headers and footers
                    if any(keyword in row_text.upper() for keyword in ["STATEMENT", "ACCOUNT", "TRANSACTION DATE", "VALUE DATE", "PARTICULARS", "DEBIT", "CREDIT", "BALANCE", "INDIAN BANK", "CLOSING BALANCE", "TOTAL DEBIT", "TOTAL CREDIT", "PAGE TOTAL", "GRAND TOTAL"]):
                        continue
                    
                    # Check for opening balance
                    if "OPENING BALANCE" in row_text.upper() or "BROUGHT FORWARD" in row_text.upper():
                        balance_match = re.search(r'([\d,]+\.\d{2})', row_text)
                        if balance_match:
                            previous_balance = balance_match.group(1)
                            if opening_balance_value is None:
                                opening_balance_value = previous_balance
                            print(f"Found opening balance: {previous_balance}")
                        continue
                    
                    # Date pattern: DD/MM/YYYY or DD/MM/YY
                    date_match = re.search(r'\b(\d{2}/\d{2}/\d{2,4})\b', row_text)
                    
                    if date_match:
                        if pending_transaction:
                            all_rows.append(pending_transaction)
                        
                        date = date_match.group(1)
                        remaining = row_text[date_match.end():].strip()
                        
                        # Pattern: amount balance
                        amount_pattern = r'([\d,]+\.\d{2})\s+([\d,]+\.\d{2})'
                        amount_match = re.search(amount_pattern, remaining)
                        
                        if amount_match:
                            amount = amount_match.group(1).replace(',', '')
                            balance = amount_match.group(2)
                            description = remaining[:amount_match.start()].strip()
                            
                            # Determine debit/credit by balance comparison
                            current_bal = float(balance.replace(',', ''))
                            prev_bal = float(previous_balance.replace(',', '')) if previous_balance else 0
                            
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
                            pending_transaction = {
                                'Date': date,
                                'Description': remaining,
                                'Debit': '',
                                'Credit': '',
                                'Balance': ''
                            }
                    else:
                        if pending_transaction:
                            amount_pattern = r'([\d,]+\.\d{2})\s+([\d,]+\.\d{2})'
                            amount_match = re.search(amount_pattern, row_text)
                            
                            if amount_match:
                                desc_part = row_text[:amount_match.start()].strip()
                                if desc_part:
                                    pending_transaction['Description'] += " " + desc_part
                                
                                amount = amount_match.group(1).replace(',', '')
                                balance = amount_match.group(2)
                                
                                current_bal = float(balance.replace(',', ''))
                                prev_bal = float(previous_balance.replace(',', '')) if previous_balance else 0
                                
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
            if pending_transaction.get('Balance') or pending_transaction.get('Debit') or pending_transaction.get('Credit'):
                all_rows.append(pending_transaction)
        
        if not all_rows:
            return None, None, None, None
        
        final_df = pd.DataFrame(all_rows)
        
        # Convert date columns to datetime type
        final_df = convert_date_columns(final_df)
        
        opening_balance = {'Balance': opening_balance_value} if opening_balance_value else None
        closing_balance = {'Balance': final_df.iloc[-1]['Balance']} if len(final_df) > 0 else None
        
        return final_df, opening_balance, closing_balance, None
        
    except Exception as e:
        print(f"Indian Bank Parser error: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None
