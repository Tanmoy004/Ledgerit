@echo off
echo Checking Ledgerit Services...
echo.

echo [1] MongoDB Status:
sc query MongoDB | find "STATE" 2>nul
if %errorlevel% neq 0 echo MongoDB service not found

echo.
echo [2] Backend Health Check:
curl -s http://localhost:5000/health 2>nul
if %errorlevel% neq 0 echo Backend not responding on port 5000

echo.
echo [3] Frontend Status:
curl -s http://localhost:3000 2>nul | find "Ledgerit" >nul
if %errorlevel% equ 0 (echo Frontend is running) else (echo Frontend not responding on port 3000)

echo.
pause