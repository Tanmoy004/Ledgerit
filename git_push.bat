@echo off
echo Initializing Git repository and pushing to GitHub...
echo.

cd /d "%~dp0"

REM Initialize git if not already initialized
if not exist ".git" (
    echo Initializing Git repository...
    git init
    echo.
)

REM Add remote if not exists
git remote remove origin 2>nul
git remote add origin https://github.com/Tanmoy004/Ledgerit.git
echo Remote added: https://github.com/Tanmoy004/Ledgerit.git
echo.

REM Add all files
echo Adding files to git...
git add .
echo.

REM Commit
echo Committing changes...
git commit -m "Complete Bank Statement Parser with Performance Analysis

- Multi-bank support (15+ Indian banks)
- OCR-based PDF processing with PaddleOCR
- Bordered and borderless table extraction
- Bank-specific parsers (JK, Indian, Canara)
- JWT authentication and subscription management
- CSV and Tally XML export
- React frontend with Tailwind CSS
- Comprehensive performance analysis
- Processing time: 8-60s depending on PDF complexity
- Main bottleneck: OCR + Table Extraction (70-85%% of time)"
echo.

REM Push to GitHub
echo Pushing to GitHub...
git branch -M main
git push -u origin main --force
echo.

echo Done! Project pushed to https://github.com/Tanmoy004/Ledgerit
pause
