import pandas as pd
from img2table.document import PDF
try:
    from img2table.ocr import PaddleOCR
except ImportError:
    # Fallback to EasyOCR if PaddleOCR is not available
    import easyocr
    class PaddleOCR:
        def __init__(self, lang="en"):
            self.reader = easyocr.Reader([lang])
        
        def __call__(self, image):
            return self.reader.readtext(image)

from pathlib import Path
import re
import PyPDF2
import io

HEADER_REGEX = re.compile(
    r"""
    \b(
        (txn\s*date|transaction\s*date|date) |
        (transaction\s*id|txn\s*id|ref\s*no) |
        (serial\s*no|s\.?\s*no|sr\s*no) |
        (debit|credit) |
        (amount|balance) |
        (particulars|description|remarks|narration)
    )\b
    """,
    re.IGNORECASE | re.VERBOSE
)

OPENING_BALANCE_REGEX = re.compile(
    r"""
    \b(
        opening\s*balance |
        b/f |
        brought\s*forward |
        balance\s*b/f |
        opening\s*bal |
        prev\s*balance
    )\b
    """,
    re.IGNORECASE | re.VERBOSE
)

CLOSING_BALANCE_REGEX = re.compile(
    r"""
    \b(
        closing\s*balance |
        c/f |
        carried\s*forward |
        balance\s*c/f |
        closing\s*bal |
        final\s*balance
    )\b
    """,
    re.IGNORECASE | re.VERBOSE
)

TRANSACTION_TOTAL_REGEX = re.compile(
    r"""
    \b(
        total\s*transactions? |
        transaction\s*total |
        total\s*amount |
        grand\s*total |
        sum\s*total |
        total\s*debit |
        total\s*credit |
        net\s*total
    )\b
    """,
    re.IGNORECASE | re.VERBOSE
)

CHEQUE_NUMBER_REGEX = re.compile(
    r"""\b(
        cheque\s*no |
        cheque\s*number |
        chq\s*no |
        chq\s*number |
        check\s*no |
        check\s*number |
        cheque\s*details |
        chq\s*details |
        check\s*details |
        instrument\s*id
    )\b""",
    re.IGNORECASE | re.VERBOSE
)

TRANSACTION_ENTRY_REGEX = re.compile(
    r"""
    (
        \d{1,2}[/-]\d{1,2}[/-]\d{2,4} |  # Date patterns DD/MM/YYYY
        \d{4}[/-]\d{1,2}[/-]\d{1,2} |    # Date patterns YYYY/MM/DD
        \d{1,2}-[A-Z]{3}-\d{4} |          # Date patterns DD-MAR-YYYY
        (upi|neft|imps|rtgs|atm|pos|cheque|transfer|payment|deposit|withdrawal|ifn|tfr) |
        [A-Z]{3}/[A-Z0-9]+ |              # Transaction codes like IFN/SMEFB257837240b00
        S\d+ |                            # Reference numbers like S65645380
        \d+\.\d{2} |                      # Amount patterns
        \b(cr|dr)\b                       # Credit/Debit indicators
    )
    """,
    re.IGNORECASE | re.VERBOSE
)

EXCLUDED_HEADER_PHRASES = [
    "Opening Balance",
    "Closing Balance", 
    "Total Debit Amount",
    "Total Credit Amount",
    "Debit Count",
    "Credit Count"
]

def has_excluded_header_phrases(row):
    """Check if row contains any excluded header phrases"""
    for cell in row.dropna():
        cell_str = str(cell).strip()
        for phrase in EXCLUDED_HEADER_PHRASES:
            if phrase.lower() in cell_str.lower():
                return True
    return False

def has_header_in_first_row(df, threshold=3):
    if df.empty:
        return False
    
    first_row = df.iloc[0]
    
    # Check if row contains excluded phrases
    if has_excluded_header_phrases(first_row):
        return False
    
    matches = 0
    for cell in first_row.dropna():
        cell_str = str(cell).strip()
        if HEADER_REGEX.search(cell_str):
            matches += 1
    
    return matches >= threshold

def has_transaction_in_first_row(df, threshold=3):
    if df.empty:
        return False
    
    first_row = df.iloc[0]
    matches = 0
    for cell in first_row.dropna():
        cell_str = str(cell).strip()
        if TRANSACTION_ENTRY_REGEX.search(cell_str):
            matches += 1
    
    return matches >= threshold

def find_best_header_row(df, threshold=2):
    best_row = -1
    best_matches = 0
    
    for i, row in df.iterrows():
        # Skip rows with excluded phrases
        if has_excluded_header_phrases(row):
            continue
            
        matches = 0
        for cell in row.dropna():
            cell_str = str(cell).strip()
            if HEADER_REGEX.search(cell_str):
                matches += 1
        
        if matches >= threshold and matches > best_matches:
            best_matches = matches
            best_row = i
    
    return best_row if best_row != -1 else None

def process_header_and_duplicates(df):
    if df.empty:
        return df
    
    # Find best header row
    header_row_idx = find_best_header_row(df)
    if header_row_idx is None:
        return df
    
    # Extract header row and set column names
    header_row = df.iloc[header_row_idx]
    columns = header_row.fillna("").astype(str).str.strip()
    
    # Handle duplicate column names
    seen = {}
    new_columns = []
    for col in columns:
        if col in seen:
            seen[col] += 1
            new_columns.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_columns.append(col)
    
    # Set new column names
    df.columns = new_columns
    
    # Remove the header row itself and any duplicate header rows
    rows_to_drop = [header_row_idx]
    for j, row in df.iterrows():
        if j != header_row_idx:
            matches = 0
            for cell in row.dropna():
                cell_str = str(cell).strip()
                if HEADER_REGEX.search(cell_str):
                    matches += 1
            if matches >= 3:
                rows_to_drop.append(j)
    
    df = df.drop(index=rows_to_drop).reset_index(drop=True)
    return df

def extract_opening_balance(df):
    if df.empty:
        return df, None
    
    first_row = df.iloc[0]
    for cell in first_row.dropna():
        cell_str = str(cell).strip()
        if OPENING_BALANCE_REGEX.search(cell_str):
            opening_balance = first_row.to_dict()
            df = df.iloc[1:].reset_index(drop=True)
            return df, opening_balance
    
    return df, None

def extract_closing_balance(df):
    if df.empty:
        return df, None
    
    last_row = df.iloc[-1]
    for cell in last_row.dropna():
        cell_str = str(cell).strip()
        if CLOSING_BALANCE_REGEX.search(cell_str):
            closing_balance = last_row.to_dict()
            df = df.iloc[:-1].reset_index(drop=True)
            return df, closing_balance
    
    return df, None

def extract_transaction_total(df):
    if df.empty:
        return df, None
    
    last_row = df.iloc[-1]
    for cell in last_row.dropna():
        cell_str = str(cell).strip()
        if TRANSACTION_TOTAL_REGEX.search(cell_str):
            transaction_total = last_row.to_dict()
            df = df.iloc[:-1].reset_index(drop=True)
            return df, transaction_total
    
    return df, None

def merge_multiline_transactions(df: pd.DataFrame, max_empty=2) -> pd.DataFrame:
    df = df.copy()
    rows_to_drop = []

    def is_empty(x):
        return pd.isna(x) or str(x).strip() == ""

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

def decrypt_pdf_bytes(pdf_bytes, password):
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    writer = PyPDF2.PdfWriter()

    try:
        result = reader.decrypt(password)
        if result == 0:
            return None
    except Exception:
        return None

    for page in reader.pages:
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()

def main():
    st.title("Bank Statement Table Detector (Bordered)")
    
    uploaded_file = st.file_uploader("Upload your statement", type=["pdf"])
    
    if not uploaded_file:
        return
    
    st.success("Statement uploaded successfully!")
    
    pdf_bytes = uploaded_file.read()
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    
    if "pdf_ready" not in st.session_state:
        st.session_state.pdf_ready = False
    
    if "decrypted_pdf_bytes" not in st.session_state:
        st.session_state.decrypted_pdf_bytes = None
    
    # Password handling
    if pdf_reader.is_encrypted and not st.session_state.pdf_ready:
        st.warning("🔐 This PDF is password protected")
        password = st.text_input("Enter PDF password", type="password")
    
        if password:
            decrypted_bytes = decrypt_pdf_bytes(pdf_bytes, password)
            if decrypted_bytes is None:
                st.error("❌ Wrong password. Please try again.")
            else:
                st.success("✅ PDF unlocked successfully!")
                st.session_state.decrypted_pdf_bytes = decrypted_bytes
                st.session_state.pdf_ready = True
                st.rerun()
        return
    
    # Load PDF
    if pdf_reader.is_encrypted:
        pdf_doc = PDF(st.session_state.decrypted_pdf_bytes)
    else:
        pdf_doc = PDF(pdf_bytes)
    
    ocr = PaddleOCR(lang="en")
    
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
    
    # Filter tables with header or transaction entry in first row
    for page_num, page_tables in pdf_tables.items():
        for table in page_tables:
            df = table.df
            if has_header_in_first_row(df) or has_transaction_in_first_row(df):
                # Check if this is the first table
                if not all_pages:
                    # Store header as list and find cheque number column
                    if has_header_in_first_row(df):
                        header_row = df.iloc[0].fillna("").astype(str).str.strip().tolist()
                    else:
                        header_row = df.columns.tolist()
                    
                    # Find cheque number column index
                    for i, col in enumerate(header_row):
                        if CHEQUE_NUMBER_REGEX.search(col):
                            cheque_column_index = i
                            break
                    
                    first_table_columns = len(df.columns)
                    all_pages.append(df)
                else:
                    # Check column count for subsequent tables
                    current_columns = len(df.columns)
                    if current_columns == first_table_columns - 1 and cheque_column_index is not None:
                        # Add empty column at cheque number index
                        df_list = df.values.tolist()
                        for row in df_list:
                            row.insert(cheque_column_index, "")
                        
                        # Create new dataframe with adjusted columns
                        new_columns = list(range(first_table_columns))
                        df = pd.DataFrame(df_list, columns=new_columns)
                    
                    all_pages.append(df)
    
    if not all_pages:
        st.warning("No transaction tables detected.")
        return
    
    # Combine all pages
    final_df = pd.concat(all_pages, ignore_index=True)
    final_df = final_df.fillna("")
    
    # Process headers and remove duplicates
    final_df = process_header_and_duplicates(final_df)
    
    # Extract opening and closing balances and transaction total
    final_df, opening_balance = extract_opening_balance(final_df)
    final_df, closing_balance = extract_closing_balance(final_df)
    final_df, transaction_total = extract_transaction_total(final_df)
    
    # Apply multiline transaction merging
    final_df = merge_multiline_transactions(final_df)
    
    # Display results
    st.subheader("Transaction Data")
    st.dataframe(final_df, use_container_width=True)
    
    # Download CSV
    csv = final_df.to_csv(index=False).encode("utf-8")
    clean_name = Path(uploaded_file.name).stem
    
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"{clean_name}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()