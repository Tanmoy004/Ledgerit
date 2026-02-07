"""
Test script to measure actual performance
Usage: python test_performance.py <path_to_pdf> [password]
"""

import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from performance_profiler import analyze_pdf_processing

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_performance.py <pdf_path> [password]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("\nStarting performance analysis...")
    print("This will process the PDF and show time taken by each segment.\n")
    
    analyze_pdf_processing(pdf_path, password)
