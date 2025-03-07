@echo off
echo ===================================
echo       LSTM股票预测系统
echo ===================================
echo.

set PYTHONPATH=%cd%

rem 检查Python环境
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误: 未找到Python，请确保Python已安装并添加到PATH中
    exit /b 1
)

rem 检查目录
if not exist "LSTM" (
    echo 错误: 未找到LSTM目录
    exit /b 1
)

rem 检查watchlist.json文件
if not exist "watchlist.json" (
    echo 警告: 未找到自选股文件watchlist.json
    set "choice="
    set /p choice="是否继续运行预测? (y/n): "
    if /i not "%choice%"=="y" exit /b 0
    goto manual_input
)

rem 从watchlist.json文件中获取股票代码
echo 正在读取自选股列表...
python -c "import json; f=open('watchlist.json', 'r', encoding='utf-8'); d=json.load(f); f.close(); codes=[s.get('code', '') for s in (d if isinstance(d, list) else d.get('stocks', [])) if 'code' in s]; print(' '.join([c for c in codes if c]))" > temp_codes.txt

set /p STOCK_CODES=<temp_codes.txt
del temp_codes.txt

echo 发现以下股票: %STOCK_CODES%
echo.

set "choice="
set /p choice="是否对这些股票运行预测? (y/n): "
if /i not "%choice%"=="y" goto manual_input

echo.
echo 开始预测选定的股票...
python -m LSTM.batch_predict %STOCK_CODES%
goto end

:manual_input
echo.
echo 请输入股票代码(多个股票用空格分隔, 如: 000001 600519):
set /p STOCK_CODES="股票代码: "

if "%STOCK_CODES%"=="" (
    echo 未输入股票代码，退出
    exit /b 0
)

echo.
echo 开始预测您输入的股票...
python -m LSTM.batch_predict %STOCK_CODES%

:end
echo.
echo ===================================
echo       预测完成
echo ===================================

pause 