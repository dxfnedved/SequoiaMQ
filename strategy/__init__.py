# 策略包初始化文件
# 所有策略类都应该实现以下接口：
# - analyze(self, data): 分析数据并返回结果
# - get_signals(self, data): 获取买卖信号

# 首先导入基类
from .base import BaseStrategy

# 然后导入具体策略类
from .RSRS import RSRS_Strategy
from .turtle_trade import TurtleStrategy
from .alpha_factors101 import Alpha101Strategy
from .alpha_factors191 import Alpha191Strategy
from .low_atr import LowATRStrategy
from .low_backtrace_increase import LowBacktraceIncreaseStrategy
from .keep_increasing import KeepIncreasingStrategy
from .backtrace_ma250 import BacktraceMA250Strategy
from .enter import EnterStrategy
from .composite_strategy import CompositeStrategy
from .news_strategy import NewsStrategy
from .alpha360 import Alpha360Strategy
from .modular_strategy import ModularStrategy

__all__ = [
    'RSRS_Strategy',
    'TurtleStrategy',
    'Alpha101Strategy',
    'Alpha191Strategy',
    'LowATRStrategy',
    'LowBacktraceIncreaseStrategy',
    'KeepIncreasingStrategy',
    'BacktraceMA250Strategy',
    'EnterStrategy',
    'CompositeStrategy',
    'NewsStrategy',
    'Alpha360Strategy',
    'ModularStrategy'
]
