import pandas as pd
import numpy as np
from strategy.alpha_factors101 import Alpha101Strategy
from strategy.RSRS import RSRS_Strategy
from strategy.turtle_trade import TurtleStrategy
from strategy.low_atr import LowATRStrategy
from strategy.alpha360 import Alpha360Strategy
from logger_manager import LoggerManager
from strategy import BaseStrategy
from strategy.alpha_factors191 import Alpha191Strategy
from strategy.enter import EnterStrategy
from strategy.keep_increasing import KeepIncreasingStrategy
from strategy.backtrace_ma250 import BacktraceMA250Strategy
from strategy.composite_strategy import CompositeStrategy


class StrategyAnalyzer:
    """策略分析器类"""
    def __init__(self, logger_manager=None):
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("strategy_analyzer")
        
        # 初始化所有策略
        self.logger.info("初始化策略分析器...")
        self.strategies = {}
        
        try:
            # 逐个初始化策略，确保单个策略失败不影响整体
            strategy_classes = {
                'Alpha101': Alpha101Strategy,
                'Alpha360': Alpha360Strategy,
                'RSRS': RSRS_Strategy,
                'Turtle': TurtleStrategy,
                'LowATR': LowATRStrategy,
                'Alpha191': Alpha191Strategy,
                'Enter': EnterStrategy,
                'KeepIncreasing': KeepIncreasingStrategy,
                'BacktraceMA250': BacktraceMA250Strategy,
                'Composite': CompositeStrategy
            }
            
            for name, strategy_class in strategy_classes.items():
                try:
                    self.strategies[name] = strategy_class(logger_manager=self.logger_manager)
                    self.logger.info(f"成功加载策略: {name}")
                except Exception as e:
                    self.logger.error(f"加载策略 {name} 失败: {str(e)}")
                    
            self.logger.info(f"共加载 {len(self.strategies)} 个策略")
            
        except Exception as e:
            self.logger.error(f"初始化策略分析器失败: {str(e)}")

    def analyze(self, data, code=None):
        """分析股票数据"""
        if data is None or data.empty:
            self.logger.warning(f"股票数据为空，无法进行分析")
            return None

        result = {}
        signal_count = {'买入': 0, '卖出': 0}
        
        try:
            # 数据预处理
            data = self._preprocess_data(data)
            
            # 运行所有策略
            for strategy_name, strategy in self.strategies.items():
                self.logger.info(f"执行{strategy_name}策略分析...")
                try:
                    strategy_result = strategy.analyze(data)
                    if strategy_result:
                        result[strategy_name] = strategy_result
                        # 检查是否有买卖信号
                        if 'signal' in strategy_result:
                            signal = strategy_result['signal']
                            if signal != "无":
                                signal_count[signal] += 1
                                self.logger.info(f"{strategy_name}策略产生{signal}信号")
                    else:
                        self.logger.info(f"{strategy_name}策略没有产生结果")
                except Exception as e:
                    self.logger.error(f"{strategy_name}策略分析失败: {str(e)}")
                    continue
            
            # 输出信号统计
            self.logger.info(f"信号统计 - 买入: {signal_count['买入']}, 卖出: {signal_count['卖出']}")
                
        except Exception as e:
            self.logger.error(f"策略分析失败: {str(e)}")
            return None
            
        return result if result else None

    def _preprocess_data(self, data):
        """数据预处理"""
        try:
            # 确保数据列名统一
            column_mapping = {
                '收盘': 'close',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            }
            
            # 重命名列
            for old_name, new_name in column_mapping.items():
                if old_name in data.columns and new_name not in data.columns:
                    data = data.rename(columns={old_name: new_name})
                    
            # 确保必要的列存在
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                self.logger.error(f"数据缺少必要列: {missing_columns}")
                return None
                
            # 删除无效数据
            data = data[data['volume'] > 0].copy()
            
            return data
            
        except Exception as e:
            self.logger.error(f"数据预处理失败: {str(e)}")
            return None