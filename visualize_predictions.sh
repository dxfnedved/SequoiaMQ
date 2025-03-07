#!/bin/bash

echo "==================================="
echo "       LSTM预测结果可视化工具"
echo "==================================="
echo

export PYTHONPATH=$(pwd)

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python，请确保Python已安装"
    exit 1
fi

# 检查目录
if [ ! -d "LSTM" ]; then
    echo "错误: 未找到LSTM目录"
    exit 1
fi

# 检查预测目录
if [ ! -d "LSTM/predictions" ]; then
    echo "警告: 未找到预测结果目录 LSTM/predictions"
    echo "可能需要先运行LSTM预测"
fi

# 检查watchlist.json文件
if [ ! -f "watchlist.json" ]; then
    echo "警告: 未找到自选股文件watchlist.json"
fi

echo "选择操作:"
echo "[1] 生成单只股票预测图表"
echo "[2] 生成自选股票预测图表"
echo "[3] 生成所有股票预测图表"
echo "[4] 生成预测摘要报告"
echo "[5] 全部生成(预测图表和摘要报告)"
echo

read -p "请选择操作(1-5): " choice

# 创建输出目录
mkdir -p "LSTM/charts"

if [ "$choice" = "1" ]; then
    echo
    echo "请输入单只股票代码:"
    read -p "股票代码: " stock_code
    
    if [ -z "$stock_code" ]; then
        echo "未输入股票代码，退出"
        exit 0
    fi
    
    echo
    echo "正在生成股票 $stock_code 的预测图表..."
    python3 -m LSTM.visualize_prediction --stock "$stock_code"
    
elif [ "$choice" = "2" ]; then
    if [ ! -f "watchlist.json" ]; then
        echo "错误: 未找到watchlist.json文件，无法获取自选股"
        exit 1
    fi
    
    echo
    echo "正在从自选股列表获取股票代码..."
    stock_codes=$(python3 -c "import json; f=open('watchlist.json', 'r', encoding='utf-8'); d=json.load(f); f.close(); codes=[s.get('code', '') for s in (d if isinstance(d, list) else d.get('stocks', [])) if 'code' in s]; print(' '.join([c for c in codes if c]))")
    
    if [ -z "$stock_codes" ]; then
        echo "未找到任何自选股票代码，退出"
        exit 0
    fi
    
    echo "发现以下股票: $stock_codes"
    echo
    echo "正在生成自选股票预测图表..."
    python3 -m LSTM.visualize_prediction --stocks $stock_codes
    
elif [ "$choice" = "3" ]; then
    echo
    echo "正在生成所有股票预测图表..."
    python3 -m LSTM.visualize_prediction --all
    
elif [ "$choice" = "4" ]; then
    echo
    echo "正在生成预测摘要报告..."
    python3 -m LSTM.visualize_prediction --report
    
elif [ "$choice" = "5" ]; then
    echo
    echo "正在生成所有预测图表和摘要报告..."
    python3 -m LSTM.visualize_prediction --all --report
    
else
    echo
    echo "无效的选择: $choice"
    echo "请输入1-5之间的数字"
    exit 1
fi

echo
echo "==================================="
echo "       预测可视化完成"
echo "==================================="

read -p "按回车键继续..." dummy 