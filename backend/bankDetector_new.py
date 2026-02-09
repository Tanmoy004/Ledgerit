def calculate_opening_balance_universal(final_df, is_reverse_chrono):
    """Universal opening balance calculation for all bank formats"""
    if len(final_df) == 0:
        return None
    
    target_row = final_df.iloc[-1] if is_reverse_chrono else final_df.iloc[0]
    balance_col = debit_col = credit_col = None
    
    for col in final_df.columns:
        col_lower = str(col).lower()
        if 'balance' in col_lower:
            balance_col = col
        elif 'debit' in col_lower or 'withdrawal' in col_lower:
            debit_col = col
        elif 'credit' in col_lower or 'deposit' in col_lower:
            credit_col = col
    
    if balance_col and debit_col and credit_col:
        try:
            balance_val = float(str(target_row[balance_col]).replace('INR', '').replace(',', '').strip())
            debit_str = str(target_row[debit_col]).replace('INR', '').replace(',', '').strip()
            credit_str = str(target_row[credit_col]).replace('INR', '').replace(',', '').strip()
            debit_val = float(debit_str) if debit_str and debit_str not in ['', '-', '0.00'] else 0.0
            credit_val = float(credit_str) if credit_str and credit_str not in ['', '-', '0.00'] else 0.0
            
            opening = balance_val + debit_val - credit_val
            return {'Balance': f'{opening:.2f}', 'Source': 'Calculated'}
        except Exception as e:
            print(f"[ERROR] Opening calc failed: {e}")
    
    return None
