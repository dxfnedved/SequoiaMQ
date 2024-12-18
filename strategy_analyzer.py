"""Strategy analyzer widget implementation."""


from datetime import datetime
from data_fetcher import DataFetcher
from logger_manager import LoggerManager
from strategy.RSRS import RSRS_Strategy
from strategy.turtle_trade import TurtleStrategy
from strategy.alpha_factors101 import Alpha101Strategy
from strategy.low_atr import LowATRStrategy
from strategy.low_backtrace_increase import LowBacktraceIncreaseStrategy
from strategy.keep_increasing import KeepIncreasingStrategy
from strategy.backtrace_ma250 import BacktraceMA250Strategy
from strategy.alpha_factors191 import Alpha191Strategy
from strategy.alpha360 import Alpha360Strategy
from strategy.enter import EnterStrategy
from strategy.composite_strategy import CompositeStrategy
from strategy.modular_strategy import ModularStrategy

class StrategyAnalyzer():
    """策略分析器"""
    
    def __init__(self, logger_manager=None):
        super().__init__()
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("strategy_analyzer")
        self.data_fetcher = DataFetcher(logger_manager=self.logger_manager)
        
        # 初始化策略
        self.strategies = {
            'RSRS_Strategy': RSRS_Strategy(logger_manager=self.logger_manager),
            'TurtleStrategy': TurtleStrategy(logger_manager=self.logger_manager),
            'Alpha101Strategy': Alpha101Strategy(logger_manager=self.logger_manager),
            'LowATRStrategy': LowATRStrategy(logger_manager=self.logger_manager),
            'LowBacktraceStrategy': LowBacktraceIncreaseStrategy(logger_manager=self.logger_manager),
            'KeepIncreasingStrategy': KeepIncreasingStrategy(logger_manager=self.logger_manager),
            'BacktraceMA250Strategy': BacktraceMA250Strategy(logger_manager=self.logger_manager),
            'Alpha191Strategy': Alpha191Strategy(logger_manager=self.logger_manager),
            'Alpha360Strategy': Alpha360Strategy(logger_manager=self.logger_manager),
            'EnterStrategy': EnterStrategy(logger_manager=self.logger_manager),
            'CompositeStrategy': CompositeStrategy(logger_manager=self.logger_manager),
            'ModularStrategy': ModularStrategy(logger_manager=self.logger_manager)
        }
        
    def analyze_stock(self, code):
        """分析单只股票
        
        Args:
            code (str): 股票代码
            
        Returns:
            dict: 分析结果，包含各个策略的信号
        """
        try:
            self.logger.info(f"开始分析股票 {code}")
            
            # 获取数据
            data = self.data_fetcher.get_stock_data({'code': code})
            if data is None:
                self.logger.error(f"获取股票 {code} 数据失败")
                return None
                
            # 预处理数据
            data = self._preprocess_data(data)
            if data is None:
                self.logger.error(f"预处理股票 {code} 数据失败")
                return None
                
            # 分析结果
            results = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'code': code,
                'data_date': data.index[-1].strftime('%Y-%m-%d')
            }
            
            # 运行每个策略
            for strategy_id, strategy in self.strategies.items():
                try:
                    strategy_result = strategy.analyze(data)
                    if strategy_result:
                        results[strategy_id] = strategy_result
                except Exception as e:
                    self.logger.error(f"策略 {strategy_id} 分析股票 {code} 失败: {str(e)}")
                    continue
                    
            self.logger.info(f"完成股票 {code} 分析")
            return results
            
        except Exception as e:
            self.logger.error(f"分析股票 {code} 失败: {str(e)}")
            return None
            
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