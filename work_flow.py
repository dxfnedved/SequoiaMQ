# -*- encoding: UTF-8 -*-

import utils
import settings
import data_fetcher
import pandas as pd
import os
from datetime import datetime
from strategy.alpha_factors101 import Alpha101Strategy
from strategy.alpha_factors191 import Alpha191Strategy
from strategy.RSRS import RSRS_Strategy
from strategy.turtle_trade import TurtleStrategy
from strategy.enter import EnterStrategy
from strategy.low_atr import LowATRStrategy
from strategy.low_backtrace_increase import LowBacktraceIncreaseStrategy
from strategy.keep_increasing import KeepIncreasingStrategy
from strategy.backtrace_ma250 import BacktraceMA250Strategy
from tqdm import tqdm
import traceback
import concurrent.futures
from logger_manager import LoggerManager

class WorkFlow:
    def __init__(self):
        # 初始化日志管理器
        self.logger_manager = LoggerManager()
        self.logger = self.logger_manager.get_logger("work_flow")
        
        # 初始化所有策略
        self.strategies = [
            Alpha101Strategy(logger_manager=self.logger_manager),
            Alpha191Strategy(logger_manager=self.logger_manager),
            RSRS_Strategy(logger_manager=self.logger_manager),
            TurtleStrategy(logger_manager=self.logger_manager),
            EnterStrategy(logger_manager=self.logger_manager),
            LowATRStrategy(logger_manager=self.logger_manager),
            LowBacktraceIncreaseStrategy(logger_manager=self.logger_manager),
            KeepIncreasingStrategy(logger_manager=self.logger_manager),
            BacktraceMA250Strategy(logger_manager=self.logger_manager)
        ]
        
        # 初始化数据获取器
        self.data_fetcher = data_fetcher.DataFetcher(self.logger_manager)
        
        # 创建结果目录
        self.setup_result_dirs()
        
    def setup_result_dirs(self):
        """设置结果目录"""
        # 基础结果目录
        self.results_dir = 'results'
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            
        # 当日结果目录（使用精确时间戳避免重复）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.today_dir = os.path.join(self.results_dir, timestamp)
        if not os.path.exists(self.today_dir):
            os.makedirs(self.today_dir)
            
    def analyze_single_stock(self, code_name_tuple):
        """分析单个股票"""
        code, name = code_name_tuple
        try:
            # 获取数据
            data = self.data_fetcher.fetch_stock_data(code)
            if data is None:
                self.logger.warning(f"获取股票 {code} {name} 数据失败")
                return None
                
            # 执行策略分析
            stock_result = {
                '股票代码': code,
                '股票名称': name,
                '分析时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 记录各策略信号
            signals = []
            for strategy in self.strategies:
                try:
                    result = strategy.analyze(data)
                    if result:
                        # 添加到分析结果
                        strategy_name = strategy.__class__.__name__
                        stock_result[f'{strategy_name}_结果'] = result
                        
                        # 获取信号
                        strategy_signals = strategy.get_signals(data)
                        if strategy_signals:
                            signals.extend(strategy_signals)
                            stock_result[f'{strategy_name}_信号'] = [s['type'] for s in strategy_signals]
                            
                except Exception as e:
                    self.logger.error(f"策略 {strategy.__class__.__name__} 分析股票 {code} 失败: {str(e)}")
                    continue
                    
            return stock_result, signals
            
        except Exception as e:
            self.logger.error(f"分析股票 {code} 失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
            
    def prepare(self):
        """准备分析任务"""
        try:
            # 获取股票列表
            stock_list = utils.get_stock_list()
            if not stock_list:
                self.logger.error("获取股票列表失败")
                return
                
            self.logger.info(f"开始分析 {len(stock_list)} 只股票")
            
            # 使用线程池并行处理
            config = settings.get_config()
            max_workers = config.get('analysis', {}).get('max_workers', 4)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_stock = {
                    executor.submit(self.analyze_single_stock, stock): stock 
                    for stock in stock_list
                }
                
                # 处理结果
                results = []
                for future in tqdm(concurrent.futures.as_completed(future_to_stock), 
                                 total=len(stock_list),
                                 desc="分析进度"):
                    stock = future_to_stock[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                    except Exception as e:
                        self.logger.error(f"处理股票 {stock[0]} 结果失败: {str(e)}")
                        
            # 保存结果
            if results:
                self.save_results(results)
                
        except Exception as e:
            self.logger.error(f"准备分析任务失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            
    def save_results(self, results):
        """保存分析结果"""
        try:
            # 转换为DataFrame
            df = pd.DataFrame([r[0] for r in results if r])
            
            # 保存到CSV文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'analysis_results_{timestamp}.csv'
            filepath = os.path.join(self.today_dir, filename)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            self.logger.info(f"分析结果已保存到: {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存分析结果失败: {str(e)}")
            self.logger.error(traceback.format_exc())


