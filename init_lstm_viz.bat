@echo off
chcp 65001 > nul
echo =================================
echo       初始化LSTM可视化工具
echo =================================
echo.

REM 创建LSTM目录结构
if not exist "LSTM" mkdir LSTM
if not exist "LSTM\predictions" mkdir LSTM\predictions
if not exist "LSTM\charts" mkdir LSTM\charts
if not exist "LSTM\reports" mkdir LSTM\reports

echo LSTM可视化工具已初始化完成
echo 目录结构：
echo   LSTM\predictions - 存放预测结果
echo   LSTM\charts - 存放生成的图表
echo   LSTM\reports - 存放分析报告
echo.
echo 请使用 visualize_predictions.bat 运行可视化工具

pause 