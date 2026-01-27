# Bank Statement Parser

A full-stack application for parsing and processing bank statements from various Indian banks with OCR capabilities and data export features.

## Features

- **Multi-Bank Support**: Supports 15+ Indian banks including SBI, HDFC, ICICI, Axis, Kotak, etc.
- **Intelligent Detection**: Automatic bank detection from PDF statements
- **OCR Processing**: Advanced OCR using PaddleOCR for text extraction
- **Data Export**: Export to CSV and Tally XML formats
- **User Authentication**: JWT-based authentication with subscription management
- **Responsive UI**: Modern React frontend with Tailwind CSS

## Tech Stack

**Backend:**
- Flask (Python web framework)
- MongoDB (Database)
- PaddleOCR (Text recognition)
- OpenCV (Image processing)
- PyPDF2/PyMuPDF (PDF processing)

**Frontend:**
- React 18
- Tailwind CSS
- Axios (HTTP client)

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- MongoDB

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```env
MONGODB_URI=mongodb://localhost:27017/ledgerit
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRES=86400
FREE_PAGE_LIMIT=100
```

4. Start the Flask server:
```bash
python flask_app.py
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

## Usage

1. **Register/Login**: Create an account or login
2. **Upload Statement**: Upload PDF bank statement (password-protected PDFs supported)
3. **Process**: System automatically detects bank and extracts transactions
4. **Export**: Download data as CSV or Tally XML

## Supported Banks

- State Bank of India (SBI)
- HDFC Bank
- ICICI Bank
- Axis Bank
- Kotak Mahindra Bank
- IndusInd Bank
- Yes Bank
- Federal Bank
- Union Bank of India
- Central Bank of India
- Punjab National Bank
- Indian Bank
- Canara Bank
- Jammu & Kashmir Bank
- And more...

## API Endpoints

- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `POST /upload` - Upload and process bank statement
- `POST /export/csv` - Export to CSV
- `POST /export/tally` - Export to Tally XML

## Project Structure

```
├── backend/
│   ├── controllers/     # Request handlers
│   ├── models/         # Data models
│   ├── routes/         # API routes
│   ├── logos/          # Bank logos for detection
│   └── flask_app.py    # Main application
├── frontend/
│   ├── src/            # React components
│   └── public/         # Static assets
└── requirements.txt    # Python dependencies
```

## License

Private Project