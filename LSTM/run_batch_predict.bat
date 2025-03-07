@echo off
echo 开始批量股票预测...

REM 设置默认参数
set STOCKS=000001 600519 601318
set MODEL_TYPE=lstm_with_thoughts
set MAX_WORKERS=4
set FUTURE_DAYS=7
set EPOCHS=20

REM 检查是否有自定义参数
if not "%1"=="" (
    set STOCKS=%*
)

echo 将预测以下股票: %STOCKS%
echo 使用模型: %MODEL_TYPE%
echo 并行线程数: %MAX_WORKERS%
echo 预测未来天数: %FUTURE_DAYS%
echo 训练轮数: %EPOCHS%

REM 创建输出目录
set OUTPUT_DIR=results\%date:~0,4%%date:~5,2%%date:~8,2%
mkdir %OUTPUT_DIR% 2>nul
mkdir %OUTPUT_DIR%\plots 2>nul

REM 运行批量预测
python batch_predict.py %STOCKS% --model_type %MODEL_TYPE% --max_workers %MAX_WORKERS% --future_days %FUTURE_DAYS% --epochs %EPOCHS% --output_dir %OUTPUT_DIR%

echo 预测完成，结果保存在 %OUTPUT_DIR% 目录
pause 