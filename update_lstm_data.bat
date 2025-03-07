@echo off
echo ===================================
echo       开始更新LSTM模型数据集
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

echo 检查数据新鲜度并更新过期数据...
python LSTM\update_dataset.py --check-freshness --max-days 3

echo.
echo 更新自选股数据...
python LSTM\update_dataset.py --watchlist

echo.
echo ===================================
echo       LSTM数据更新完成
echo ===================================

timeout /t 3 >nul 