# -*- encoding: UTF-8 -*-

import utils
import settings
import data_fetcher
import pandas as pd
import os
from datetime import datetime
from strategy import (
    RSRS_Strategy,
    Alpha101Strategy,
    Alpha191Strategy,
    TurtleStrategy,
    EnterStrategy,
    LowATRStrategy,
    LowBacktraceIncreaseStrategy,
    KeepIncreasingStrategy,
    BacktraceMA250Strategy
)
from logger_manager import LoggerManager
import traceback
from tqdm import tqdm
import concurrent.futures

class WorkFlow:
    def __init__(self):
        # 初始化日志管理器
        self.logger_manager = LoggerManager()
        self.logger = self.logger_manager.get_logger("work_flow")
        
        # 初始化策略
        self.strategies = [
            Alpha101Strategy(),
            RSRS_Strategy(),
            Alpha191Strategy(),
            TurtleStrategy(),
            EnterStrategy(),
            LowATRStrategy(),
            LowBacktraceIncreaseStrategy(),
            KeepIncreasingStrategy(),
            BacktraceMA250Strategy()
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
            
        # 当日结果目录
        self.today_dir = os.path.join(self.results_dir, datetime.now().strftime('%Y%m%d'))
        if not os.path.exists(self.today_dir):
            os.makedirs(self.today_dir)
            
        # 当前时间目录
        self.current_time_dir = os.path.join(self.today_dir, datetime.now().strftime('%H%M%S'))
        if not os.path.exists(self.current_time_dir):
            os.makedirs(self.current_time_dir)
            
    def analyze_single_stock(self, stock):
        """分析单个股票"""
        try:
            # 处理股票代码和名称
            code = stock[0] if isinstance(stock, tuple) else stock
            name = stock[1] if isinstance(stock, tuple) else None
            
            # 获取股票数据
            data = self.data_fetcher.fetch_stock_data(stock)
            if data is None or len(data) == 0:
                self.logger.warning(f"获取股票 {stock} 数据失败")
                return None
                
            # 分析数据
            stock_result = {
                '股票代码': code,
                '股票名称': name
            }
            signals = []
            
            for strategy in self.strategies:
                try:
                    result = strategy.analyze(data)
                    if result:
                        # 添加策略结果到stock_result
                        for key, value in result.items():
                            stock_result[f"{strategy.name}_{key}"] = value
                            
                        # 检查是否有信号
                        signal = result.get('signal', None)
                        if signal and signal != '无':
                            signals.append((strategy.name, signal))
                            
                except Exception as e:
                    self.logger.error(f"策略 {strategy.name} 分析失败: {str(e)}")
                    
            return (stock_result, signals) if stock_result else None
            
        except Exception as e:
            self.logger.error(f"分析股票 {stock} 失败: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None
            
    def prepare(self):
        """准备数据并执行分析"""
        try:
            # 获取股票列表
            stock_list = utils.get_stock_list()
            if not stock_list:
                self.logger.error("获取股票列表失败")
                return
                
            # 获取配置
            config = settings.get_config()
            batch_size = config.get('batch_size', 100)
            use_parallel = config.get('analysis', {}).get('parallel', True)
            max_workers = config.get('analysis', {}).get('max_workers', 4)
            
            # 初始化结果列表
            analysis_results = []
            signal_results = []
            resonance_results = []
            
            self.logger.info(f"开始分析 {len(stock_list)} 只股票...")
            
            if use_parallel:
                # 并行处理
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {executor.submit(self.analyze_single_stock, stock): stock for stock in stock_list}
                    
                    with tqdm(total=len(stock_list), desc="分析进度") as pbar:
                        for future in concurrent.futures.as_completed(futures):
                            stock = futures[future]
                            try:
                                result = future.result()
                                if result:
                                    stock_result, signals = result
                                    
                                    # 添加分析结果
                                    analysis_results.append(stock_result)
                                    
                                    # 添加信号结果
                                    for strategy_name, signal in signals:
                                        signal_results.append({
                                            '股票代码': stock[0],
                                            '股票名称': stock[1],
                                            '策略名称': strategy_name,
                                            '信号类型': signal,
                                            '触发时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        })
                                        
                                    # 检查策略共振
                                    if len(signals) >= 2:
                                        resonance_results.append({
                                            '股票代码': stock[0],
                                            '股票名称': stock[1],
                                            '共振策略': ', '.join(s[0] for s in signals),
                                            '共振信号': '; '.join(s[1] for s in signals),
                                            '共振强度': len(signals),
                                            '触发时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        })
                            except Exception as e:
                                self.logger.error(f"处理股票 {stock[0]} 结果时出错: {str(e)}")
                            pbar.update(1)
            else:
                # 串行处理
                for stock in tqdm(stock_list, desc="分析进度"):
                    result = self.analyze_single_stock(stock)
                    if result:
                        stock_result, signals = result
                        
                        # 添加分析结果
                        analysis_results.append(stock_result)
                        
                        # 添加信号结果
                        for strategy_name, signal in signals:
                            signal_results.append({
                                '股票代码': stock[0],
                                '股票名称': stock[1],
                                '策略名称': strategy_name,
                                '信号类型': signal,
                                '触发时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            
                        # 检查策略共振
                        if len(signals) >= 2:
                            resonance_results.append({
                                '股票代码': stock[0],
                                '股票名称': stock[1],
                                '共振策略': ', '.join(s[0] for s in signals),
                                '共振信号': '; '.join(s[1] for s in signals),
                                '共振强度': len(signals),
                                '触发时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            
            # 导出结果
            self.export_results(analysis_results, signal_results, resonance_results)
            
        except Exception as e:
            self.logger.error(f"执行分析流程失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            
    def export_results(self, analysis_results, signal_results, resonance_results):
        """导出分析结果"""
        try:
            # 导出分析结果
            if analysis_results:
                analysis_df = pd.DataFrame(analysis_results)
                analysis_file = os.path.join(self.current_time_dir, 'analysis_results.csv')
                analysis_df.to_csv(analysis_file, index=False, encoding='utf-8-sig')
                self.logger.info(f"分析结果已导出到: {analysis_file}")
                
            # 导出信号结果
            if signal_results:
                signal_df = pd.DataFrame(signal_results)
                signal_file = os.path.join(self.current_time_dir, 'signal_results.csv')
                signal_df.to_csv(signal_file, index=False, encoding='utf-8-sig')
                self.logger.info(f"信号结果已导出到: {signal_file}")
                
            # 导出共振结果
            if resonance_results:
                resonance_df = pd.DataFrame(resonance_results)
                resonance_file = os.path.join(self.current_time_dir, 'resonance_results.csv')
                resonance_df.to_csv(resonance_file, index=False, encoding='utf-8-sig')
                self.logger.info(f"共振结果已导出到: {resonance_file}")
                
            # 输出统计信息
            self.logger.info(f"分析完成的股票数: {len(analysis_results)}")
            self.logger.info(f"触发信号的股票数: {len(set(r['股票代码'] for r in signal_results))}")
            self.logger.info(f"发生策略共振的股票数: {len(resonance_results)}")
            
        except Exception as e:
            self.logger.error(f"导出结果失败: {str(e)}")
            self.logger.error(traceback.format_exc())


