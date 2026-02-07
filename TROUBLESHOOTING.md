# Troubleshooting Guide

## "Service temporarily unavailable" Error

### Quick Fix:
1. Run `start.bat` to start all services
2. Wait 10 seconds for services to initialize
3. Check `http://localhost:5000/health` in browser

### Manual Steps:
1. **Start MongoDB:**
   ```
   net start MongoDB
   ```

2. **Start Backend:**
   ```
   cd backend
   python flask_app.py
   ```

3. **Start Frontend:**
   ```
   cd frontend
   npm start
   ```

### Common Issues:

**Port 5000 occupied:**
- Change port in `backend/flask_app.py` line 462: `port=5001`
- Update `frontend/.env`: `REACT_APP_API_URL=http://localhost:5001`

**MongoDB not running:**
- Install: Download from mongodb.com
- Start service: `net start MongoDB`

**Dependencies missing:**
- Backend: `pip install -r requirements.txt`
- Frontend: `npm install`

### Health Checks:
- Backend: http://localhost:5000/health
- Frontend: http://localhost:3000
- Check services: Run `check-services.bat`