import pandas as pd
import numpy as np
from strategy.alpha_factors101 import Alpha101Strategy
from strategy.RSRS import RSRS_Strategy
from strategy.turtle_trade import TurtleStrategy
from strategy.low_atr import LowATRStrategy
from logger_manager import LoggerManager

class StrategyAnalyzer:
    """策略分析器类"""
    def __init__(self, logger_manager=None):
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("strategy_analyzer")
        
        # 初始化所有策略
        self.strategies = {
            'Alpha101': Alpha101Strategy(logger_manager=self.logger_manager),
            'RSRS': RSRS_Strategy(logger_manager=self.logger_manager),
            'Turtle': TurtleStrategy(logger_manager=self.logger_manager),
            'LowATR': LowATRStrategy(logger_manager=self.logger_manager)
        }

    def analyze(self, data, code=None):
        """
        分析股票数据
        :param data: DataFrame 股票数据
        :param code: str 股票代码（可选）
        :return: dict 分析结果
        """
        if data is None or data.empty:
            self.logger.warning(f"股票数据为空，无法进行分析")
            return None

        result = {}
        
        try:
            # 运行Alpha101策略
            alpha_result = self.strategies['Alpha101'].analyze(data)
            if alpha_result:
                result.update(alpha_result)
                
            # 运行RSRS策略
            rsrs_result = self.strategies['RSRS'].analyze(data)
            if rsrs_result:
                result.update(rsrs_result)
                
            # 运行海龟策略
            turtle_result = self.strategies['Turtle'].analyze(data)
            if turtle_result:
                result.update(turtle_result)
                
            # 运行低ATR策略
            low_atr_result = self.strategies['LowATR'].analyze(data)
            if low_atr_result:
                result.update(low_atr_result)
                
        except Exception as e:
            self.logger.error(f"策略分析失败: {str(e)}")
            return None
            
        return result if result else None 