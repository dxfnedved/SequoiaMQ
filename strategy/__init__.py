# 策略包初始化文件
# 所有策略类都应该实现以下接口：
# - analyze(self, data): 分析数据并返回结果
# - get_signals(self, data): 获取买卖信号

# 首先导入基类
from .base import BaseStrategy

# 然后导入具体策略类
from .RSRS import RSRS_Strategy
from .alpha_factors101 import Alpha101Strategy
from .alpha_factors191 import Alpha191Strategy
from .turtle_trade import TurtleStrategy
from .enter import EnterStrategy
from .low_atr import LowATRStrategy
from .low_backtrace_increase import LowBacktraceIncreaseStrategy
from .keep_increasing import KeepIncreasingStrategy
from .backtrace_ma250 import BacktraceMA250Strategy
from .composite_strategy import CompositeStrategy
from .alpha360 import Alpha360Strategy

__all__ = [
    'BaseStrategy',
    'RSRS_Strategy',
    'Alpha101Strategy',
    'Alpha191Strategy',
    'TurtleStrategy',
    'EnterStrategy',
    'LowATRStrategy',
    'LowBacktraceIncreaseStrategy',
    'KeepIncreasingStrategy',
    'BacktraceMA250Strategy',
    'CompositeStrategy',
    'Alpha360Strategy'
]
