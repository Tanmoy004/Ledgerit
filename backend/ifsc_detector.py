import re

IFSC_BANK_MAP = {
    'SBIN': 'State Bank of India',
    'HDFC': 'HDFC Bank',
    'ICIC': 'ICICI Bank',
    'UTIB': 'Axis Bank',
    'KKBK': 'Kotak Mahindra Bank',
    'INDB': 'IndusInd Bank',
    'YESB': 'Yes Bank',
    'FDRL': 'Federal Bank',
    'UBIN': 'Union Bank of India',
    'CBIN': 'Central Bank of India',
    'PUNB': 'Punjab National Bank',
    'IDIB': 'Indian Bank',
    'CNRB': 'Canara Bank',
    'JAKA': 'Jammu and Kashmir Bank',
    'IOBA': 'Indian Overseas Bank',
    'IDBI': 'IDBI Bank',
    'BDBL': 'Bandhan Bank',
    'UCBA': 'UCO Bank'
}

def extract_ifsc_from_text(text):
    """Extract IFSC code from text"""
    ifsc_pattern = r'\b([A-Z]{4}0[A-Z0-9]{6})\b'
    matches = re.findall(ifsc_pattern, text)
    return matches[0] if matches else None

def get_bank_from_ifsc(ifsc_code):
    """Get bank name from IFSC code"""
    if not ifsc_code or len(ifsc_code) < 4:
        return None
    bank_code = ifsc_code[:4]
    return IFSC_BANK_MAP.get(bank_code)
