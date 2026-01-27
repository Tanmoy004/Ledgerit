# Authentication & Subscription System Setup Guide

## Prerequisites
1. MongoDB installed and running on localhost:27017
2. Python 3.8+ installed
3. Node.js and npm installed

## Backend Setup

1. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   - Update `.env` file with your settings:
   ```
   MONGODB_URI=mongodb://localhost:27017/ledgerit
   JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
   JWT_ACCESS_TOKEN_EXPIRES=86400
   FREE_PAGE_LIMIT=100
   ```

3. **Start MongoDB:**
   ```bash
   mongod
   ```

4. **Run Flask server:**
   ```bash
   python flask_app.py
   ```

## Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start React app:**
   ```bash
   npm start
   ```

## Features Implemented

### Authentication
- **Signup**: Create new user account with 100 free pages
- **Login**: User authentication with JWT tokens
- **Logout**: Secure token invalidation
- **Profile**: View user stats and usage

### Subscription System
- **Free Plan**: 100 pages limit for new users
- **Monthly Plan**: ₹800 for unlimited processing
- **Quarterly Plan**: ₹2000 for 3 months (17% savings)
- **Yearly Plan**: ₹3000 for 12 months (69% savings)

### Page Tracking
- Automatic PDF page counting
- Usage tracking per user
- Subscription validation before processing
- Redirect to subscription page when limit reached

## API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile

### Subscription
- `GET /api/subscription/plans` - Get all plans
- `POST /api/subscription/subscribe` - Subscribe to plan
- `GET /api/subscription/status` - Get subscription status

### PDF Processing (Protected)
- `POST /upload` - Upload and process PDF (requires authentication)

## Database Schema

### Users Collection
```javascript
{
  _id: ObjectId,
  email: String,
  password: String (hashed),
  name: String,
  pages_used: Number,
  free_pages_limit: Number,
  subscription: {
    plan: String, // 'free', 'monthly', 'quarterly', 'yearly'
    status: String, // 'active', 'expired'
    start_date: Date,
    end_date: Date,
    pages_limit: Number
  },
  created_at: Date,
  updated_at: Date
}
```

## Security Features
- Password hashing with bcrypt
- JWT token authentication
- Token blacklisting for logout
- Input validation and sanitization
- CORS protection

## Usage Flow
1. User signs up → Gets 100 free pages
2. User uploads PDF → Pages counted and deducted
3. When limit reached → Redirected to subscription page
4. User subscribes → Gets unlimited access
5. Subscription expires → Back to free tier limits

## Payment Integration (Future)
The current system is demo-ready. For production:
1. Integrate Razorpay/Stripe for payments
2. Add webhook handlers for payment confirmation
3. Implement subscription renewal logic
4. Add invoice generation

## Testing
1. Create a user account
2. Upload PDFs to test page counting
3. Reach the 100-page limit
4. Test subscription upgrade flow
5. Verify unlimited access after subscription