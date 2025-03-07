#!/bin/bash

echo "==================================="
echo "       LSTM股票预测系统"
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

# 检查watchlist.json文件
if [ ! -f "watchlist.json" ]; then
    echo "警告: 未找到自选股文件watchlist.json"
    read -p "是否继续运行预测? (y/n): " choice
    if [[ ! "$choice" =~ ^[Yy]$ ]]; then
        exit 0
    fi
    manual_input=true
else
    manual_input=false
    # 从watchlist.json文件中获取股票代码
    echo "正在读取自选股列表..."
    STOCK_CODES=$(python3 -c "import json; f=open('watchlist.json', 'r', encoding='utf-8'); d=json.load(f); f.close(); codes=[s.get('code', '') for s in (d if isinstance(d, list) else d.get('stocks', [])) if 'code' in s]; print(' '.join([c for c in codes if c]))")

    echo "发现以下股票: $STOCK_CODES"
    echo
    
    read -p "是否对这些股票运行预测? (y/n): " choice
    if [[ ! "$choice" =~ ^[Yy]$ ]]; then
        manual_input=true
    fi
fi

if [ "$manual_input" = true ]; then
    echo
    echo "请输入股票代码(多个股票用空格分隔, 如: 000001 600519):"
    read -p "股票代码: " STOCK_CODES
    
    if [ -z "$STOCK_CODES" ]; then
        echo "未输入股票代码，退出"
        exit 0
    fi
fi

echo
echo "开始预测选定的股票..."
python3 -m LSTM.batch_predict $STOCK_CODES

echo
echo "==================================="
echo "       预测完成"
echo "==================================="

read -p "按回车键继续..." dummy 