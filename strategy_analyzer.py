import pandas as pd
import numpy as np
from strategy.alpha_factors101 import Alpha101Strategy
from strategy.RSRS import RSRS_Strategy
from strategy.turtle_trade import TurtleStrategy
from strategy.low_atr import LowATRStrategy
from strategy.composite_strategy import CompositeStrategy
from strategy.backtrace_ma250 import BacktraceMA250Strategy
from strategy.alpha_factors191 import Alpha191Strategy
from logger_manager import LoggerManager

class StrategyAnalyzer:
    """策略分析器类"""
    def __init__(self, logger_manager=None):
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("strategy_analyzer")
        
        # 初始化所有策略
        print("初始化策略分析器...")
        self.strategies = {
            'Alpha101': Alpha101Strategy(logger_manager=self.logger_manager),
            'RSRS': RSRS_Strategy(logger_manager=self.logger_manager),
            'Turtle': TurtleStrategy(logger_manager=self.logger_manager),
            'LowATR': LowATRStrategy(logger_manager=self.logger_manager),
            'Composite': CompositeStrategy(logger_manager=self.logger_manager),
            'BacktraceMA250': BacktraceMA250Strategy(logger_manager=self.logger_manager),
            'Alpha191': Alpha191Strategy(logger_manager=self.logger_manager)
        }
        print(f"已加载 {len(self.strategies)} 个策略")

    def analyze(self, data, code=None):
        """
        分析股票数据
        :param data: DataFrame 股票数据
        :param code: str 股票代码（可选）
        :return: dict 分析结果
        """
        if data is None or data.empty:
            print(f"股票数据为空，无法进行分析")
            self.logger.warning(f"股票数据为空，无法进行分析")
            return None

        result = {}
        
        try:
            # 运行所有策略
            for strategy_name, strategy in self.strategies.items():
                print(f"执行{strategy_name}策略分析...")
                try:
                    strategy_result = strategy.analyze(data)
                    if strategy_result:
                        result[strategy_name] = strategy_result
                        # 检查是否有买卖信号
                        if 'signal' in strategy_result and strategy_result['signal'] != "无":
                            print(f"{strategy_name}策略产生{strategy_result['signal']}信号")
                    else:
                        print(f"{strategy_name}策略没有产生结果")
                except Exception as e:
                    error_msg = f"{strategy_name}策略分析失败: {str(e)}"
                    print(error_msg)
                    self.logger.error(error_msg)
                    continue
                
        except Exception as e:
            error_msg = f"策略分析失败: {str(e)}"
            print(error_msg)
            self.logger.error(error_msg)
            return None
            
        return result if result else None