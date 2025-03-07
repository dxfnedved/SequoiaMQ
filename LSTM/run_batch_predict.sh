#!/bin/bash

echo "开始批量股票预测..."

# 设置默认参数
STOCKS="000001 600519 601318"
MODEL_TYPE="lstm_with_thoughts"
MAX_WORKERS=4
FUTURE_DAYS=7
EPOCHS=20

# 检查是否有自定义参数
if [ $# -gt 0 ]; then
    STOCKS="$@"
fi

echo "将预测以下股票: $STOCKS"
echo "使用模型: $MODEL_TYPE"
echo "并行线程数: $MAX_WORKERS"
echo "预测未来天数: $FUTURE_DAYS"
echo "训练轮数: $EPOCHS"

# 创建输出目录
OUTPUT_DIR="results/$(date +%Y%m%d)"
mkdir -p "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/plots"

# 运行批量预测
python batch_predict.py $STOCKS --model_type $MODEL_TYPE --max_workers $MAX_WORKERS --future_days $FUTURE_DAYS --epochs $EPOCHS --output_dir $OUTPUT_DIR

echo "预测完成，结果保存在 $OUTPUT_DIR 目录" 