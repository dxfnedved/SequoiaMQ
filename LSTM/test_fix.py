import numpy as np
from datetime import datetime, timedelta
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 模拟预测结果
future_days = 3
future_dates = [datetime.now() + timedelta(days=i+1) for i in range(future_days)]

# 创建不同类型的预测结果进行测试
predictions = [
    np.array([10.5]),                    # 简单numpy数组
    np.array([[11.2]]),                  # 嵌套numpy数组
    np.array([12.8], dtype=np.float32),  # 不同数据类型
    [13.4],                              # Python列表
    14.7                                 # 单个浮点数
]

print("开始测试格式化修复...")

# 测试每种情况
for i, (date, pred) in enumerate(zip(future_dates, predictions)):
    print(f"\n测试案例 {i+1}:")
    print(f"预测值类型: {type(pred)}")
    if isinstance(pred, (list, np.ndarray)) and len(pred) > 0:
        print(f"预测值[0]类型: {type(pred[0])}")
    
    try:
        # 尝试直接格式化 - 这可能会失败
        print(f"直接格式化: {date.strftime('%Y-%m-%d')}: {pred[0] if isinstance(pred, (list, np.ndarray)) else pred:.2f}")
    except Exception as e:
        print(f"直接格式化失败: {str(e)}")
    
    try:
        # 使用修复后的方法
        if isinstance(pred, (list, np.ndarray)):
            if isinstance(pred[0], (list, np.ndarray)):
                pred_value = float(pred[0][0])
            else:
                pred_value = float(pred[0])
        else:
            pred_value = float(pred)
        print(f"修复后格式化: {date.strftime('%Y-%m-%d')}: {pred_value:.2f}")
    except Exception as e:
        print(f"修复后格式化失败: {str(e)}")

print("\n测试完成!") 