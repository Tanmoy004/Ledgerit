import pandas as pd
import re
from img2table.document import PDF
from img2table.ocr import PaddleOCR
import PyPDF2
import io

def get_ocr_instance():
    return PaddleOCR(lang="en")

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
        opening_balance_value = None
        closing_balance_value = None
        pending_transaction = None
        
        for page_num, page_tables in pdf_tables.items():
            for table in page_tables:
                df = table.df
                
                if len(df) < 3:
                    continue
                
                for idx, row in df.iterrows():
                    row_text = " ".join([str(cell) for cell in row if pd.notna(cell) and str(cell).strip()])
                    
                    if not row_text.strip():
                        continue
                    
                    # Skip header/metadata rows and summary content
                    if any(keyword in row_text.upper() for keyword in ["CURRENCY", "EMAIL", "IFSC", "STATEMENT", "CLEARED BALANCE", "UNCLEARED", "NOMINEE", "CKYC", "DR. COUNT", "CR. COUNT", "IN CASE YOUR ACCOUNT", "WITH EXTRA CARE"]):
                        continue
                    
                    # Check for Brought Forward (opening balance)
                    if "BROUGHT FORWARD" in row_text.upper():
                        balance_match = re.search(r'([\d,]+\.?\d*(?:Cr|Dr))', row_text)
                        if balance_match and opening_balance_value is None:
                            opening_balance_value = balance_match.group(1)
                        continue
                    
                    # Check for Carried Forward (skip but continue processing)
                    if "CARRIED FORWARD" in row_text.upper():
                        continue
                    
                    # Check for Closing Balance
                    if "CLOSING BALANCE" in row_text.upper():
                        balance_match = re.search(r'([\d,]+\.?\d*(?:Cr|Dr))', row_text)
                        if balance_match:
                            closing_balance_value = balance_match.group(1)
                        continue
                    
                    # Check for date pattern DD/MM/YY
                    date_match = re.search(r'\b(\d{2}/\d{2}/\d{2})\b', row_text)
                    
                    if date_match:
                        # If we have a pending transaction, save it first
                        if pending_transaction:
                            all_rows.append(pending_transaction)
                        
                        date = date_match.group(1)
                        
                        # Extract the rest after first date
                        remaining = row_text[date_match.end():].strip()
                        
                        # Look for second date (Value Date)
                        second_date_match = re.search(r'\b(\d{2}/\d{2}/\d{2})\b', remaining)
                        if second_date_match:
                            value_date = second_date_match.group(1)
                            remaining = remaining[second_date_match.end():].strip()
                        else:
                            value_date = date
                        
                        # Extract amounts and balance from the end
                        # Pattern: ...description... amount balance
                        amount_balance_pattern = r'([\d,]+\.?\d*)\s+([\d,]+\.?\d*(?:Cr|Dr))\s*$'
                        amount_match = re.search(amount_balance_pattern, remaining)
                        
                        if amount_match:
                            amount = amount_match.group(1).replace(',', '')
                            balance = amount_match.group(2)
                            description = remaining[:amount_match.start()].strip()
                            
                            # Determine if debit or credit based on description keywords
                            desc_lower = description.lower()
                            if any(word in desc_lower for word in ['transfer to', 'charges', 'debit']):
                                debit = amount
                                credit = ''
                            else:
                                debit = ''
                                credit = amount
                            
                            pending_transaction = {
                                'Post Date': date,
                                'Value Date': value_date,
                                'Details': description,
                                'Chq.No.': '',
                                'Debit': debit,
                                'Credit': credit,
                                'Balance': balance
                            }
                        else:
                            # Only balance at end
                            balance_pattern = r'([\d,]+\.?\d*(?:Cr|Dr))\s*$'
                            balance_match = re.search(balance_pattern, remaining)
                            
                            if balance_match:
                                balance = balance_match.group(1)
                                description = remaining[:balance_match.start()].strip()
                                
                                pending_transaction = {
                                    'Post Date': date,
                                    'Value Date': value_date,
                                    'Details': description,
                                    'Chq.No.': '',
                                    'Debit': '',
                                    'Credit': '',
                                    'Balance': balance
                                }
                            else:
                                # Start a new transaction without amounts (multi-line)
                                pending_transaction = {
                                    'Post Date': date,
                                    'Value Date': value_date,
                                    'Details': remaining,
                                    'Chq.No.': '',
                                    'Debit': '',
                                    'Credit': '',
                                    'Balance': ''
                                }
                    else:
                        # This might be a continuation line
                        if pending_transaction:
                            # Check if this line has amounts
                            amount_balance_pattern = r'([\d,]+\.?\d*)\s+([\d,]+\.?\d*(?:Cr|Dr))\s*$'
                            amount_match = re.search(amount_balance_pattern, row_text)
                            
                            if amount_match:
                                amount = amount_match.group(1).replace(',', '')
                                balance = amount_match.group(2)
                                desc_part = row_text[:amount_match.start()].strip()
                                
                                if desc_part:
                                    pending_transaction['Details'] += ' ' + desc_part
                                
                                # Determine if debit or credit
                                desc_lower = pending_transaction['Details'].lower()
                                if any(word in desc_lower for word in ['transfer to', 'charges', 'debit', 'chq']):
                                    pending_transaction['Debit'] = amount
                                    pending_transaction['Credit'] = ''
                                else:
                                    pending_transaction['Debit'] = ''
                                    pending_transaction['Credit'] = amount
                                
                                pending_transaction['Balance'] = balance
                            else:
                                # Just add to description
                                pending_transaction['Details'] += ' ' + row_text.strip()
        
        # Add any pending transaction
        if pending_transaction:
            all_rows.append(pending_transaction)
        
        if not all_rows:
            return None, None, None, None
        
        final_df = pd.DataFrame(all_rows)
        
        # Opening balance is the Brought Forward balance
        opening_balance = {'Balance': opening_balance_value} if opening_balance_value else None
        print(f"Opening balance (Brought Forward): {opening_balance}")
        
        # Closing balance - use explicit closing balance if found, otherwise last transaction
        closing_balance = None
        if closing_balance_value:
            closing_balance = {'Balance': closing_balance_value}
            print(f"Closing balance (from statement): {closing_balance}")
        elif len(final_df) > 0:
            closing_balance = {'Balance': final_df.iloc[-1]['Balance']}
            print(f"Closing balance (from last transaction): {closing_balance}")
        
        return final_df, opening_balance, closing_balance, None
        
    except Exception as e:
        print(f"Indian Bank Parser error: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None