#!/bin/bash

echo "==================================="
echo "      开始更新LSTM模型数据集"
echo "==================================="
echo

# 设置PYTHONPATH
export PYTHONPATH=$(pwd)

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "错误: 未找到Python，请确保Python已安装"
    exit 1
fi

# 检查目录
if [ ! -d "LSTM" ]; then
    echo "错误: 未找到LSTM目录"
    exit 1
fi

echo "检查数据新鲜度并更新过期数据..."
python LSTM/update_dataset.py --check-freshness --max-days 3

echo
echo "更新自选股数据..."
python LSTM/update_dataset.py --watchlist

echo
echo "==================================="
echo "      LSTM数据更新完成"
echo "==================================="

sleep 3 