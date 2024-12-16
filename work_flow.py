# -*- encoding: UTF-8 -*-

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_fetcher import DataFetcher
from strategy_analyzer import StrategyAnalyzer
from logger_manager import LoggerManager
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import traceback
from tqdm import tqdm
from colorama import init, Fore, Style
import random
import utils

# 初始化colorama，确保在Windows上也能正常显示颜色
init(autoreset=True)

def process_stock_data(args):
    """处理单个股票数据的线程函数"""
    stock, logger_manager = args
    logger = logger_manager.get_logger("process_stock")
    
    try:
        data_fetcher = DataFetcher(logger_manager=logger_manager)
        strategy_analyzer = StrategyAnalyzer(logger_manager=logger_manager)
        
        # 处理股票代码和名称
        if isinstance(stock, dict):
            code = stock['code']
            name = stock['name']
        elif isinstance(stock, (list, tuple)):
            code = stock[0]
            name = stock[1]
        else:
            code = str(stock)
            name = "Unknown"
            
        # 获取数据
        data = data_fetcher.get_stock_data(stock)
        if data is None or data.empty:
            return None
            
        # 记录数据来源
        from_cache = data_fetcher.is_from_cache(code)
        
        # 分析数据
        result = strategy_analyzer.analyze(data, code)
        
        if result:
            # 预处理结果
            processed_result = {
                'code': code,
                'name': name,
                'buy_signals': 0,
                'sell_signals': 0,
                'strategies': [],
                'signal_details': [],
                'from_cache': from_cache,
                'data_date': data.index[-1].strftime('%Y-%m-%d')
            }
            
            # 统计买入卖出信号
            for strategy_name, strategy_result in result.items():
                if isinstance(strategy_result, dict) and 'signal' in strategy_result:
                    signal = strategy_result['signal']
                    if signal == '买入':
                        processed_result['buy_signals'] += 1
                        processed_result['strategies'].append(f"{strategy_name}(买入)")
                        processed_result['signal_details'].append({
                            'strategy': strategy_name,
                            'type': '买入',
                            'factors': strategy_result.get('factors', {}),
                            'strength': strategy_result.get('buy_signals', 1)
                        })
                    elif signal == '卖出':
                        processed_result['sell_signals'] += 1
                        processed_result['strategies'].append(f"{strategy_name}(卖出)")
                        processed_result['signal_details'].append({
                            'strategy': strategy_name,
                            'type': '卖出',
                            'factors': strategy_result.get('factors', {}),
                            'strength': strategy_result.get('sell_signals', 1)
                        })
            
            return processed_result
            
        return None
        
    except Exception as e:
        logger.error(f"处理股票 {code} 时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return None

class WorkFlow:
    """工作流程类"""
    def __init__(self, logger_manager=None):
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("workflow")
        self.data_fetcher = DataFetcher(logger_manager=self.logger_manager)
        self.strategy_analyzer = StrategyAnalyzer(logger_manager=self.logger_manager)
        self.analysis_results = []
        self.stock_names = utils.get_stock_name_dict()
        
        # 性能优化参数
        self.max_workers = min(32, (os.cpu_count() or 1) * 4)  # 线程数
        self.batch_size = 50  # 批处理大小
        
    def prepare(self):
        """准备并执行分析流程"""
        try:
            print("\n开始准备分析流程...")
            self.logger.info("开始准备分析流程...")
            
            # 创建必要的目录
            for dir_name in ['data', 'cache', 'logs', 'summary']:
                os.makedirs(dir_name, exist_ok=True)
            
            # 获取股票列表
            print("正在获取股票列表...")
            self.logger.info("获取股票列表...")
            stock_list = utils.get_stock_list()
            if not stock_list:
                self.logger.error("获取股票列表失败")
                return False
            
            print(f"成功获取 {len(stock_list)} 只股票")
            self.logger.info(f"成功获取 {len(stock_list)} 只股票")
            
            # 分析股票
            print("\n开始分析股票...")
            self.logger.info("开始分析股票...")
            results = self.analyze_stocks(stock_list)
            
            if results:
                self.analysis_results = results
                # 生成汇总报告
                print("\n正在生成分析报告...")
                self.logger.info("生成分析报告...")
                self.generate_summary_report()
                print("分析流程完成")
                self.logger.info("分析流程完成")
                return True
            else:
                print("分析股票失败")
                self.logger.error("分析股票失败")
                return False
                
        except Exception as e:
            print(f"准备分析流程时出错: {str(e)}")
            self.logger.error(f"准备分析流程时出错: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False
            
    def analyze_stocks(self, stock_list):
        """使用多线程分析股票"""
        try:
            # 初始化统计信息
            start_time = time.time()
            total_stocks = len(stock_list)
            results = []
            success_count = 0
            error_count = 0
            cache_hit_count = 0
            
            # 创建进度条
            progress_bar = tqdm(
                total=total_stocks,
                desc=f"{Fore.BLUE}分析进度{Style.RESET_ALL}",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
                ncols=100,
                unit="只"
            )
            
            # 使用线程池处理
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_stock = {
                    executor.submit(process_stock_data, (stock, self.logger_manager)): stock 
                    for stock in stock_list
                }
                
                # 处理完成的任务
                for future in as_completed(future_to_stock):
                    stock = future_to_stock[future]
                    try:
                        result = future.result()
                        if result:
                            success_count += 1
                            if result.get('from_cache', False):
                                cache_hit_count += 1
                            results.append(result)
                        else:
                            error_count += 1
                            
                        # 更新进度条
                        progress_bar.update(1)
                        progress_bar.set_postfix({
                            '成功': f"{Fore.GREEN}{success_count}{Style.RESET_ALL}",
                            '失败': f"{Fore.RED}{error_count}{Style.RESET_ALL}",
                            '缓存': cache_hit_count
                        }, refresh=True)
                        
                        # 定期显示统计信息
                        if (success_count + error_count) % 10 == 0:
                            elapsed_time = time.time() - start_time
                            avg_time = elapsed_time / (success_count + error_count)
                            self._print_statistics(success_count, error_count, 
                                                cache_hit_count, avg_time)
                            
                    except Exception as e:
                        self.logger.error(f"处理股票 {stock} 失败: {str(e)}")
                        error_count += 1
                        progress_bar.update(1)
                        
            # 关闭进度条
            progress_bar.close()
            
            # 打印最终统计信息
            total_time = time.time() - start_time
            self._print_final_statistics(total_stocks, success_count, error_count,
                                      cache_hit_count, total_time)
            
            return results
            
        except Exception as e:
            self.logger.error(f"分析股票失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
            
    def _print_statistics(self, success_count, error_count, cache_hit_count, avg_time):
        """打印阶段性统计信息"""
        print(f"\n{Fore.YELLOW}{'-' * 50}")
        print(f"""处理统计:
{Fore.CYAN}- 成功: {success_count}
{Fore.RED}- 失败: {error_count}
{Fore.GREEN}- 缓存命中: {cache_hit_count}
{Fore.BLUE}- 平均耗时: {avg_time:.1f}秒/股
{Fore.MAGENTA}- 缓存命中率: {(cache_hit_count/(success_count + error_count)*100) if (success_count + error_count) > 0 else 0:.1f}%{Style.RESET_ALL}
""")
        print(f"{Fore.YELLOW}{'-' * 50}{Style.RESET_ALL}")
        
    def _print_final_statistics(self, total_stocks, success_count, error_count,
                              cache_hit_count, total_time):
        """打印最终统计信息"""
        print(f"\n{Fore.GREEN}{'=' * 50}")
        print(f"""{Fore.CYAN}分析完成:
{Fore.WHITE}总数量: {total_stocks}
{Fore.GREEN}处理成功: {success_count}
{Fore.RED}处理失败: {error_count}
{Fore.YELLOW}总用时: {total_time/60:.1f}分钟
{Fore.BLUE}平均耗时: {total_time/total_stocks if total_stocks > 0 else 0:.1f}秒/股
{Fore.MAGENTA}缓存命中率: {(cache_hit_count/(success_count + error_count)*100) if (success_count + error_count) > 0 else 0:.1f}%{Style.RESET_ALL}
""")
        print(f"{Fore.GREEN}{'=' * 50}{Style.RESET_ALL}")


