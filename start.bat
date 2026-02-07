@echo off
echo ========================================
echo Starting Ledgerit Application
echo ========================================

echo.
echo [1/3] Starting MongoDB...
net start MongoDB >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ MongoDB started successfully
) else (
    echo ⚠ MongoDB may already be running or failed to start
)

echo.
echo [2/3] Starting Backend Server...
cd backend
start "Ledgerit Backend" cmd /k "python flask_app.py"
timeout /t 3 >nul

echo.
echo [3/3] Starting Frontend...
cd ..\frontend
start "Ledgerit Frontend" cmd /k "npm start"

echo.
echo ========================================
echo All services started!
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo Health Check: http://localhost:5000/health
echo ========================================
pause