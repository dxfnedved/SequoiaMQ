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
from strategy.news_strategy import NewsStrategy

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
            'ModularStrategy': ModularStrategy(logger_manager=self.logger_manager),
        }
        
        # 初始化新闻策略（单独处理）
        self.news_strategy = NewsStrategy(logger_manager=self.logger_manager)
        self.news_analysis_result = None
        self.news_analysis_time = None
        
    def perform_news_analysis(self):
        """执行全局新闻分析，每个会话只执行一次"""
        try:
            self.logger.info("开始执行全局新闻分析...")
            
            # 获取全局新闻分析结果
            self.news_analysis_result = self.news_strategy.perform_global_analysis()
            if self.news_analysis_result:
                self.news_analysis_time = datetime.now()
                self.logger.info("全局新闻分析完成")
                return True
            else:
                self.logger.warning("全局新闻分析未产生结果")
                return False
                
        except Exception as e:
            self.logger.error(f"执行全局新闻分析时发生错误: {str(e)}")
            return False
            
    def analyze_stock(self, stock_code):
        """分析单个股票"""
        try:
            # 获取股票数据
            stock_data = self.data_fetcher.get_stock_data(stock_code)
            if stock_data is None or stock_data.empty:
                self.logger.warning(f"无法获取股票 {stock_code} 的数据")
                return None
            
            # 预处理数据
            processed_data = self._preprocess_data(stock_data)
            if processed_data is None:
                self.logger.warning(f"股票 {stock_code} 的数据预处理失败")
                return None
            
            # 运行所有策略
            strategy_results = {}
            for strategy_name, strategy in self.strategies.items():
                try:
                    result = strategy.analyze(processed_data)
                    if result:
                        strategy_results[strategy_name] = result
                except Exception as e:
                    self.logger.error(f"策略 {strategy_name} 分析股票 {stock_code} 时出错: {str(e)}")
            
            # 添加新闻策略结果（如果有）
            if self.news_analysis_result:
                try:
                    news_result = self.news_strategy.analyze(processed_data)
                    if news_result:
                        strategy_results['NewsStrategy'] = news_result
                except Exception as e:
                    self.logger.error(f"新闻策略分析股票 {stock_code} 时出错: {str(e)}")
                
            if not strategy_results:
                self.logger.warning(f"股票 {stock_code} 没有产生任何策略结果")
                return None
            
            # 添加时间戳到分析结果
            analysis_result = {
                'code': stock_code,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'strategy_results': strategy_results,
                'last_price': float(processed_data['close'].iloc[-1]),
                'last_volume': float(processed_data['volume'].iloc[-1]),
                'last_date': processed_data.index[-1].strftime('%Y-%m-%d')
            }
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"分析股票 {stock_code} 时发生错误: {str(e)}")
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