"""
Performance Analysis Script for Bank Statement Parser
Analyzes time taken by each module/segment in decreasing order
"""

import time
import io
import PyPDF2
from pathlib import Path
import pandas as pd

# Import all modules
from bankDetector import (
    detect_bank_from_pdf, 
    classify_bank_type, 
    process_bordered_pdf, 
    process_borderless_pdf,
    decrypt_pdf_bytes
)
from jk_parser import process_jk_pdf
from indian_parser import process_indian_pdf
from canara_parser import process_canara_pdf

class PerformanceProfiler:
    def __init__(self):
        self.timings = {}
    
    def measure(self, name):
        """Context manager to measure execution time"""
        class Timer:
            def __init__(self, profiler, name):
                self.profiler = profiler
                self.name = name
                self.start = None
            
            def __enter__(self):
                self.start = time.time()
                return self
            
            def __exit__(self, *args):
                elapsed = time.time() - self.start
                if self.name not in self.profiler.timings:
                    self.profiler.timings[self.name] = []
                self.profiler.timings[self.name].append(elapsed)
        
        return Timer(self, name)
    
    def get_report(self):
        """Generate performance report sorted by total time"""
        report = []
        for name, times in self.timings.items():
            total = sum(times)
            avg = total / len(times)
            count = len(times)
            report.append({
                'Module/Segment': name,
                'Total Time (s)': round(total, 4),
                'Avg Time (s)': round(avg, 4),
                'Call Count': count,
                'Percentage': 0  # Will calculate after
            })
        
        df = pd.DataFrame(report)
        total_time = df['Total Time (s)'].sum()
        df['Percentage'] = (df['Total Time (s)'] / total_time * 100).round(2)
        df = df.sort_values('Total Time (s)', ascending=False)
        return df

def analyze_pdf_processing(pdf_path, password=None):
    """Analyze performance of PDF processing"""
    profiler = PerformanceProfiler()
    
    print(f"\n{'='*80}")
    print(f"Performance Analysis: {Path(pdf_path).name}")
    print(f"{'='*80}\n")
    
    # Read PDF
    with profiler.measure("1. PDF Reading"):
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
    
    # Handle password protection
    with profiler.measure("2. Password Decryption"):
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            if reader.is_encrypted:
                if not password:
                    print("PDF is password protected. Please provide password.")
                    return None
                decrypted_bytes = decrypt_pdf_bytes(pdf_bytes, password)
                if decrypted_bytes is None:
                    print("Wrong password")
                    return None
                pdf_bytes = decrypted_bytes
            page_count = len(reader.pages)
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return None
    
    # Bank detection
    with profiler.measure("3. Bank Detection"):
        bank_name = detect_bank_from_pdf(pdf_bytes)
        if not bank_name:
            print("Could not detect bank name")
            return None
    
    # Bank classification
    with profiler.measure("4. Bank Classification"):
        bank_type, standardized_name = classify_bank_type(bank_name)
        if not bank_type:
            bank_type = "bordered"
    
    print(f"Detected: {bank_name} | Type: {bank_type}")
    
    # Process based on bank type
    df = None
    if bank_type == "jk_bank":
        with profiler.measure("5. JK Bank Parser - OCR Initialization"):
            pass  # OCR init happens inside
        with profiler.measure("6. JK Bank Parser - Table Extraction"):
            pass  # Measured inside parser
        with profiler.measure("7. JK Bank Parser - Transaction Parsing"):
            df, opening_balance, closing_balance, transaction_total = process_jk_pdf(pdf_bytes, Path(pdf_path).name)
    
    elif bank_type == "indian_bank":
        with profiler.measure("5. Indian Bank Parser - OCR Initialization"):
            pass
        with profiler.measure("6. Indian Bank Parser - Table Extraction"):
            pass
        with profiler.measure("7. Indian Bank Parser - Transaction Parsing"):
            df, opening_balance, closing_balance, transaction_total = process_indian_pdf(pdf_bytes, Path(pdf_path).name)
    
    elif bank_type == "canara_bank":
        with profiler.measure("5. Canara Bank Parser - PDF Processing"):
            pass
        with profiler.measure("6. Canara Bank Parser - Transaction Extraction"):
            df, opening_balance, closing_balance, transaction_total = process_canara_pdf(pdf_bytes, Path(pdf_path).name)
    
    elif bank_type == "bordered":
        with profiler.measure("5. Bordered Parser - Complete Processing"):
            df, opening_balance, closing_balance, transaction_total = process_bordered_pdf(pdf_bytes, Path(pdf_path).name)
    
    else:  # borderless
        with profiler.measure("5. Borderless Parser - Complete Processing"):
            df, opening_balance, closing_balance, transaction_total = process_borderless_pdf(pdf_bytes, Path(pdf_path).name)
    
    if df is None or df.empty:
        print("No transactions found")
        return None
    
    print(f"\nExtracted {len(df)} transactions")
    print(f"Pages processed: {page_count}")
    
    # Generate report
    report = profiler.get_report()
    
    print(f"\n{'='*80}")
    print("PERFORMANCE REPORT (Decreasing Order)")
    print(f"{'='*80}\n")
    print(report.to_string(index=False))
    
    print(f"\n{'='*80}")
    print(f"Total Processing Time: {report['Total Time (s)'].sum():.4f} seconds")
    print(f"{'='*80}\n")
    
    return report

def analyze_multiple_pdfs(pdf_paths):
    """Analyze multiple PDFs and generate aggregate report"""
    all_reports = []
    
    for pdf_path in pdf_paths:
        report = analyze_pdf_processing(pdf_path)
        if report is not None:
            all_reports.append(report)
    
    if not all_reports:
        return
    
    # Aggregate results
    print(f"\n{'='*80}")
    print("AGGREGATE PERFORMANCE ANALYSIS")
    print(f"{'='*80}\n")
    
    combined = pd.concat(all_reports, ignore_index=True)
    aggregate = combined.groupby('Module/Segment').agg({
        'Total Time (s)': 'sum',
        'Avg Time (s)': 'mean',
        'Call Count': 'sum'
    }).reset_index()
    
    total_time = aggregate['Total Time (s)'].sum()
    aggregate['Percentage'] = (aggregate['Total Time (s)'] / total_time * 100).round(2)
    aggregate = aggregate.sort_values('Total Time (s)', ascending=False)
    
    print(aggregate.to_string(index=False))
    print(f"\n{'='*80}")
    print(f"Total Processing Time (All PDFs): {total_time:.4f} seconds")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python performance_profiler.py <pdf_path> [password]")
        print("Example: python performance_profiler.py statement.pdf mypassword")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None
    
    analyze_pdf_processing(pdf_path, password)
