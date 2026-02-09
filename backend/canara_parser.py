# canara_parser.py
import re
import pdfplumber
from datetime import datetime
import pandas as pd
import io
from dateutil import parser as date_parser

def merge_multiline_transactions(df: pd.DataFrame, max_empty=2) -> pd.DataFrame:
    """Merge multiline transactions - same logic as other parsers"""
    df = df.copy()
    rows_to_drop = []

    def is_empty(x):
        return pd.isna(x) or str(x).strip() == "" or str(x).strip() == "-"

    base_row_idx = None

    for i in range(1, len(df)):
        row = df.iloc[i]
        empty_count = sum(is_empty(v) for v in row)

        if empty_count <= max_empty:
            base_row_idx = i
            continue

        if base_row_idx is not None:
            for col in df.columns:
                curr_val = df.at[i, col]

                if not is_empty(curr_val):
                    base_val = df.at[base_row_idx, col]

                    if is_empty(base_val):
                        df.at[base_row_idx, col] = str(curr_val).strip()
                    else:
                        df.at[base_row_idx, col] = (
                            str(base_val).strip() + " " + str(curr_val).strip()
                        )

            rows_to_drop.append(i)

    df.drop(index=rows_to_drop, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

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

class Transaction:
    def __init__(self, date, description, debit, credit, balance, bank_name):
        self.date = date
        self.description = description
        self.debit = debit
        self.credit = credit
        self.balance = balance
        self.bank_name = bank_name

class CanaraBankTransactionParser:
    def parse_transactions(self, pdf_path, password=None):
        all_transactions = []
        
        with pdfplumber.open(pdf_path, password=password) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                transactions = self._extract_from_text(text)
                all_transactions.extend(transactions)
        
        return all_transactions
    
    def _extract_from_text(self, text):
        transactions = []
        lines = text.split('\n')
        
        # Filter out page headers
        filtered_lines = []
        for line in lines:
            line = line.strip()
            if not re.match(r'^page\s+\d+$', line, re.IGNORECASE):
                filtered_lines.append(line)
        lines = filtered_lines
        
        # Get opening balance from first page
        prev_balance = None
        for line in lines:
            if 'Opening Balance' in line:
                balance_match = re.search(r'Opening Balance\s+([0-9,]+\.?\d*)', line)
                if balance_match:
                    prev_balance = self._parse_amount(balance_match.group(1))
                break
        
        # Find start of transactions (after header/opening balance)
        start_idx = 0
        for i, line in enumerate(lines):
            if ('Date Particulars' in line or 'Opening Balance' in line or 
                re.match(r'\d{2}-\d{2}-\d{4}', line.strip())):
                if 'Date Particulars' in line or 'Opening Balance' in line:
                    start_idx = i + 1
                else:
                    start_idx = i
                break
        
        # Collect transaction blocks
        i = start_idx
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for date pattern
            if re.match(r'\d{2}-\d{2}-\d{4}', line):
                # Found date line, now collect the complete transaction
                date_line_idx = i
                
                # Collect description lines before the date (going backwards)
                desc_start_idx = date_line_idx
                for j in range(date_line_idx - 1, start_idx - 1, -1):
                    prev_line = lines[j].strip()
                    if (prev_line.startswith('Chq:') or 
                        re.match(r'\d{2}-\d{2}-\d{4}', prev_line) or
                        'Date Particulars' in prev_line or
                        'Opening Balance' in prev_line):
                        break
                    desc_start_idx = j
                
                # Collect all lines from description start to Chq: line
                tx_lines = []
                for k in range(desc_start_idx, len(lines)):
                    tx_lines.append(lines[k])
                    if lines[k].strip().startswith('Chq:'):
                        i = k + 1
                        break
                    if (k > date_line_idx and 
                        (re.match(r'\d{2}-\d{2}-\d{4}', lines[k].strip()) or
                         'Closing Balance' in lines[k])):
                        i = k
                        break
                else:
                    i = len(lines)
                
                tx = self._parse_transaction(tx_lines, prev_balance, date_line_idx - desc_start_idx)
                if tx:
                    transactions.append(tx)
                    prev_balance = tx.balance
            else:
                i += 1
        
        return transactions
    
    def _parse_transaction(self, lines, prev_balance, date_line_idx):
        try:
            # Find the date line
            date_line = lines[date_line_idx]
            date_match = re.match(r'(\d{2}-\d{2}-\d{4})', date_line)
            if not date_match:
                return None
            
            date_str = date_match.group(1)
            date = self._parse_date(date_str)
            if not date:
                return None
            
            # Extract amounts from the date line
            date_line_amounts = re.findall(r'([0-9,]+\.\d{2})', date_line)
            
            if len(date_line_amounts) < 1:
                return None
            
            # Last amount in date line is usually the balance
            balance = self._parse_amount(date_line_amounts[-1])
            
            # Determine transaction amount and type
            debit = 0
            credit = 0
            full_text = ' '.join(lines)
            
            if len(date_line_amounts) >= 2:
                transaction_amount = self._parse_amount(date_line_amounts[-2])
                
                if prev_balance is not None:
                    diff = balance - prev_balance
                    if abs(diff) > 0.01:
                        if diff < 0:
                            debit = abs(diff)
                        else:
                            credit = diff
                    else:
                        if any(keyword in full_text.upper() for keyword in ['UPI/DR', 'NACH', 'WITHDRAWAL', 'ATM', 'DEBIT', '/DR/']):
                            debit = transaction_amount
                        else:
                            credit = transaction_amount
                else:
                    if any(keyword in full_text.upper() for keyword in ['UPI/DR', 'NACH', 'WITHDRAWAL', 'ATM', 'DEBIT', '/DR/']):
                        debit = transaction_amount
                    else:
                        credit = transaction_amount
            elif prev_balance is not None:
                diff = balance - prev_balance
                if diff < 0:
                    debit = abs(diff)
                elif diff > 0:
                    credit = diff
            
            # Extract description from lines before date to Chq: line
            description_parts = []
            
            # Add description lines before date
            for i in range(date_line_idx):
                line = lines[i].strip()
                if line and not re.match(r'^[0-9,]+\.\d{2}$', line):
                    description_parts.append(line)
            
            # Add any description from date line (after removing date and amounts)
            desc_line = re.sub(r'\d{2}-\d{2}-\d{4}', '', date_line)
            for amount in date_line_amounts:
                desc_line = desc_line.replace(amount, '')
            desc_line = desc_line.strip()
            if desc_line:
                description_parts.append(desc_line)
            
            # Add lines after date up to and including Chq: line
            for i in range(date_line_idx + 1, len(lines)):
                line = lines[i].strip()
                if line and not re.match(r'^[0-9,]+\.\d{2}$', line):
                    description_parts.append(line)
                    if line.startswith('Chq:'):
                        break
            
            description = ' '.join(description_parts).strip()
            
            return Transaction(
                date=date,
                description=description,
                debit=debit,
                credit=credit,
                balance=balance,
                bank_name='CANARA'
            )
        except Exception as e:
            return None
    
    def _parse_date(self, date_str):
        try:
            # Parse "02-04-2024" format
            dt = datetime.strptime(date_str, '%d-%m-%Y')
            return dt.strftime('%Y-%m-%d')
        except:
            return None
    
    def _parse_amount(self, amount_str):
        try:
            return round(float(amount_str.replace(',', '')), 2)
        except:
            return 0.0

def process_canara_pdf(pdf_bytes, filename):
    """Process Canara Bank PDF and return DataFrame with transaction data"""
    parser = CanaraBankTransactionParser()
    
    # Save bytes to temporary file for pdfplumber
    with open('temp_canara.pdf', 'wb') as f:
        f.write(pdf_bytes)
    
    try:
        transactions = parser.parse_transactions('temp_canara.pdf')
        
        if not transactions:
            return None, None, None, None
        
        # Convert to DataFrame with proper column headers
        data = []
        for tx in transactions:
            data.append({
                'Date': tx.date,
                'Particulars': tx.description,
                'Deposits': f'{tx.credit:.2f}' if tx.credit > 0 else '',
                'Withdrawals': f'{tx.debit:.2f}' if tx.debit > 0 else '',
                'Balance': f'{tx.balance:.2f}'
            })
        
        df = pd.DataFrame(data)
        
        # Apply multiline transaction merging
        df = merge_multiline_transactions(df)
        
        # Convert date columns to datetime type
        df = convert_date_columns(df)
        
        # Extract balances - fix opening balance calculation
        if transactions:
            first_tx = transactions[0]
            # Opening balance = current balance + debit - credit
            opening_bal_amount = first_tx.balance + first_tx.debit - first_tx.credit
            opening_balance = {'Balance': f'{opening_bal_amount:.2f}'}
            closing_balance = {'Balance': f'{transactions[-1].balance:.2f}'}
        else:
            opening_balance = None
            closing_balance = None
        
        return df, opening_balance, closing_balance, None
        
    except Exception as e:
        return None, None, None, None
    finally:
        # Clean up temp file
        try:
            import os
            os.remove('temp_canara.pdf')
        except:
            pass