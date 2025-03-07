"""Strategy analyzer widget implementation."""

import os
import json
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import pandas as pd
import numpy as np

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
        
        # 策略优先级配置（数字越小优先级越高）
        self.strategy_priorities = {
            'RSRS_Strategy': 1,
            'TurtleStrategy': 2,
            'LowATRStrategy': 3,
            'LowBacktraceStrategy': 3,
            'KeepIncreasingStrategy': 3,
            'BacktraceMA250Strategy': 3,
            'Alpha101Strategy': 4,
            'Alpha191Strategy': 4,
            'Alpha360Strategy': 4,
            'EnterStrategy': 2,
            'CompositeStrategy': 1,
            'ModularStrategy': 2,
            'NewsStrategy': 5
        }
        
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
        
        # 策略结果缓存
        self.strategy_cache_dir = os.path.join('cache', 'strategy_results')
        os.makedirs(self.strategy_cache_dir, exist_ok=True)
        self.cache_duration = 24 * 60 * 60  # 24小时，单位：秒
        
        # 并行执行配置
        self.max_workers = min(32, (os.cpu_count() or 1) * 4)
        
        # 技术指标缓存
        self._indicator_cache = {}
        
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
    
    def _get_cached_result(self, stock_code, strategy_name):
        """获取缓存的策略结果"""
        try:
            cache_file = os.path.join(self.strategy_cache_dir, f"{stock_code}_{strategy_name}.json")
            
            if not os.path.exists(cache_file):
                return None
                
            # 检查缓存是否过期
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if (datetime.now() - file_time).total_seconds() > self.cache_duration:
                return None
                
            # 读取缓存
            with open(cache_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
                
            return result
            
        except Exception as e:
            self.logger.warning(f"读取策略缓存失败 {stock_code}_{strategy_name}: {str(e)}")
            return None
            
    def _save_cached_result(self, stock_code, strategy_name, result):
        """保存策略结果到缓存"""
        try:
            cache_file = os.path.join(self.strategy_cache_dir, f"{stock_code}_{strategy_name}.json")
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            self.logger.warning(f"保存策略缓存失败 {stock_code}_{strategy_name}: {str(e)}")
            return False
    
    def _calculate_technical_indicators(self, data):
        """计算常用技术指标并缓存"""
        try:
            # 使用数据的最后更新时间作为缓存键
            cache_key = f"{data.index[-1].strftime('%Y%m%d')}_{len(data)}"
            
            # 如果缓存中已有结果，直接返回
            if cache_key in self._indicator_cache:
                return self._indicator_cache[cache_key]
                
            # 计算常用技术指标
            indicators = {}
            
            # 移动平均线
            for period in [5, 10, 20, 30, 60, 120, 250]:
                indicators[f'ma{period}'] = data['close'].rolling(window=period).mean()
                
            # 指数移动平均线
            for period in [5, 10, 20, 30, 60]:
                indicators[f'ema{period}'] = data['close'].ewm(span=period, adjust=False).mean()
                
            # 布林带 (20日)
            ma20 = indicators['ma20']
            std20 = data['close'].rolling(window=20).std()
            indicators['upper_band'] = ma20 + 2 * std20
            indicators['lower_band'] = ma20 - 2 * std20
            
            # MACD
            ema12 = data['close'].ewm(span=12, adjust=False).mean()
            ema26 = data['close'].ewm(span=26, adjust=False).mean()
            indicators['macd'] = ema12 - ema26
            indicators['macd_signal'] = indicators['macd'].ewm(span=9, adjust=False).mean()
            indicators['macd_hist'] = indicators['macd'] - indicators['macd_signal']
            
            # RSI
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            for period in [6, 12, 14, 24]:
                avg_gain = gain.rolling(window=period).mean()
                avg_loss = loss.rolling(window=period).mean()
                rs = avg_gain / avg_loss.replace(0, 0.001)  # 避免除零
                indicators[f'rsi{period}'] = 100 - (100 / (1 + rs))
                
            # 存入缓存
            self._indicator_cache[cache_key] = indicators
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"计算技术指标失败: {str(e)}")
            return {}
            
    def _execute_strategy(self, strategy_name, strategy, data, stock_code):
        """执行单个策略分析"""
        try:
            # 检查缓存
            cached_result = self._get_cached_result(stock_code, strategy_name)
            if cached_result:
                self.logger.debug(f"使用缓存的策略结果: {stock_code}_{strategy_name}")
                return cached_result
                
            # 执行策略分析
            start_time = time.time()
            result = strategy.analyze(data)
            execution_time = time.time() - start_time
            
            # 添加执行时间信息
            if result:
                result['execution_time'] = execution_time
                
                # 保存到缓存
                self._save_cached_result(stock_code, strategy_name, result)
                
            return result
            
        except Exception as e:
            self.logger.error(f"执行策略 {strategy_name} 分析股票 {stock_code} 时出错: {str(e)}")
            return None
            
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
                
            # 计算常用技术指标
            indicators = self._calculate_technical_indicators(processed_data)
            
            # 按优先级对策略进行排序
            sorted_strategies = sorted(
                self.strategies.items(),
                key=lambda x: self.strategy_priorities.get(x[0], 999)
            )
            
            # 并行执行策略分析
            strategy_results = {}
            
            # 高优先级策略串行执行（优先级1-2）
            for strategy_name, strategy in sorted_strategies:
                if self.strategy_priorities.get(strategy_name, 999) <= 2:
                    result = self._execute_strategy(strategy_name, strategy, processed_data, stock_code)
                    if result:
                        strategy_results[strategy_name] = result
            
            # 其余策略并行执行
            parallel_strategies = [
                (strategy_name, strategy) for strategy_name, strategy in sorted_strategies
                if self.strategy_priorities.get(strategy_name, 999) > 2
            ]
            
            if parallel_strategies:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_strategy = {
                        executor.submit(
                            self._execute_strategy, 
                            strategy_name, 
                            strategy, 
                            processed_data, 
                            stock_code
                        ): strategy_name
                        for strategy_name, strategy in parallel_strategies
                    }
                    
                    for future in as_completed(future_to_strategy):
                        strategy_name = future_to_strategy[future]
                        try:
                            result = future.result()
                            if result:
                                strategy_results[strategy_name] = result
                        except Exception as e:
                            self.logger.error(f"并行执行策略 {strategy_name} 时出错: {str(e)}")
            
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
                'last_date': processed_data.index[-1].strftime('%Y-%m-%d'),
                'indicators': {
                    'ma5': float(indicators.get('ma5', pd.Series()).iloc[-1]) if 'ma5' in indicators else None,
                    'ma20': float(indicators.get('ma20', pd.Series()).iloc[-1]) if 'ma20' in indicators else None,
                    'ma60': float(indicators.get('ma60', pd.Series()).iloc[-1]) if 'ma60' in indicators else None,
                    'rsi14': float(indicators.get('rsi14', pd.Series()).iloc[-1]) if 'rsi14' in indicators else None,
                }
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
            
            # 填充缺失值
            for col in required_columns:
                if data[col].isnull().any():
                    # 使用前向填充
                    data[col] = data[col].fillna(method='ffill')
                    # 如果仍有缺失值（如第一行），使用后向填充
                    data[col] = data[col].fillna(method='bfill')
            
            # 计算额外的基础指标
            # 计算涨跌幅
            if 'pct_change' not in data.columns:
                data['pct_change'] = data['close'].pct_change() * 100
                
            # 计算振幅
            if 'amplitude' not in data.columns:
                data['amplitude'] = (data['high'] - data['low']) / data['close'].shift(1) * 100
                
            # 计算成交量变化
            if 'volume_change' not in data.columns:
                data['volume_change'] = data['volume'].pct_change() * 100
                
            # 计算均线
            for period in [5, 10, 20, 60, 120]:
                col_name = f'ma{period}'
                if col_name not in data.columns:
                    data[col_name] = data['close'].rolling(window=period).mean()
            
            return data
            
        except Exception as e:
            self.logger.error(f"数据预处理失败: {str(e)}")
            return None