@echo off
chcp 65001 > nul
echo ===================================
echo       LSTM Prediction Visualizer
echo ===================================
echo.

REM Set Python path
set PYTHONPATH=%cd%

REM Check Python environment
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found
    goto :end
)

REM Check directories
if not exist "LSTM" (
    echo Error: LSTM directory not found
    goto :end
)

REM Check prediction directory
if not exist "LSTM\predictions" (
    echo Warning: Prediction directory not found
    echo You may need to run LSTM prediction first
)

REM Check watchlist.json file
if not exist "watchlist.json" (
    echo Warning: watchlist.json not found
)

echo Select operation:
echo [1] Generate chart for single stock
echo [2] Generate charts for watchlist stocks
echo [3] Generate charts for all stocks
echo [4] Generate prediction summary report
echo [5] Generate all (charts and report)
echo.

set /p choice=Select operation (1-5): 

REM Create output directory
if not exist "LSTM\charts" mkdir LSTM\charts

if "%choice%"=="1" (
    echo.
    echo Enter stock code:
    set /p stock_code=Stock code: 
    
    if "%stock_code%"=="" (
        echo No stock code entered, exiting
        goto :end
    )
    
    echo.
    echo Generating chart for stock %stock_code%...
    python -m LSTM.visualize_prediction --stock %stock_code%
    if %errorlevel% neq 0 (
        echo Error generating chart
        goto :end
    )
    
) else if "%choice%"=="2" (
    if not exist "watchlist.json" (
        echo Error: watchlist.json not found
        goto :end
    )
    
    echo.
    echo Getting stock codes from watchlist...
    
    REM Extract stock codes from watchlist.json using a simpler approach
    python -c "import json; f=open('watchlist.json', 'r', encoding='utf-8'); d=json.load(f); f.close(); codes=[s.get('code', '') for s in (d if isinstance(d, list) else d.get('stocks', [])) if 'code' in s]; print(' '.join([c for c in codes if c]))" > temp_codes.txt
    set /p stock_codes=<temp_codes.txt
    del temp_codes.txt
    
    if "%stock_codes%"=="" (
        echo No stock codes found, exiting
        goto :end
    )
    
    echo Found stocks: %stock_codes%
    echo.
    echo Generating charts for watchlist stocks...
    python -m LSTM.visualize_prediction --stocks %stock_codes%
    
) else if "%choice%"=="3" (
    echo.
    echo Generating charts for all stocks...
    python -m LSTM.visualize_prediction --all
    
) else if "%choice%"=="4" (
    echo.
    echo Generating prediction summary report...
    python -m LSTM.visualize_prediction --report
    
) else if "%choice%"=="5" (
    echo.
    echo Generating all charts and summary report...
    python -m LSTM.visualize_prediction --all --report
    
) else (
    echo.
    echo Invalid choice: %choice%
    echo Please enter a number between 1 and 5
    goto :end
)

echo.
echo ===================================
echo       Visualization Complete
echo ===================================

:end
pause 