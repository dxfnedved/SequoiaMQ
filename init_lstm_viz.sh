#!/bin/bash

# 创建LSTM目录结构
mkdir -p LSTM/predictions LSTM/charts LSTM/reports

# 赋予可执行权限
chmod +x visualize_predictions.sh

echo "LSTM可视化工具已初始化完成"
echo "目录结构："
echo "  LSTM/predictions - 存放预测结果"
echo "  LSTM/charts - 存放生成的图表"
echo "  LSTM/reports - 存放分析报告"
echo 
echo "请使用 ./visualize_predictions.sh 运行可视化工具" 