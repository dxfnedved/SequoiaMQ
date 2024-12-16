# -*- encoding: UTF-8 -*-

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from data_fetcher import DataFetcher
from strategy_analyzer import StrategyAnalyzer
from logger_manager import LoggerManager
from utils import get_stock_list
import sys
from multiprocessing import Pool, cpu_count
import time
import traceback
from tqdm import tqdm
from colorama import init, Fore, Back, Style
import random
import utils  # 添加utils模块导入

# 初始化colorama
init(autoreset=True)

def get_stock_name_dict():
    """获取股票代码到名称的映射字典"""
    stock_list = get_stock_list()
    return {code: name for code, name in stock_list}

def process_stock(args):
    """处理单个股票的静态方法（用于多进程）"""
    stock, logger_manager, checkpoint_file = args
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
        
        # 检查是否已处理过
        if os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, 'r') as f:
                    processed_stocks = json.load(f)
                if code in processed_stocks:
                    return None
            except Exception as e:
                logger.error(f"读取检查点文件失败: {str(e)}")
                processed_stocks = []
        else:
            processed_stocks = []
        
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
            
            processed_result['analysis_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 只保存有信号的结果
            if processed_result['buy_signals'] > 0 or processed_result['sell_signals'] > 0:
                try:
                    # 保存分析结果
                    result_file = f'data/analysis_{code}_{datetime.now().strftime("%Y%m%d")}.json'
                    with open(result_file, 'w', encoding='utf-8') as f:
                        json.dump(processed_result, f, indent=2, ensure_ascii=False)
                    
                    # 更新检查点
                    processed_stocks.append(code)
                    with open(checkpoint_file, 'w') as f:
                        json.dump(processed_stocks, f)
                        
                    return processed_result
                    
                except Exception as e:
                    logger.error(f"保存股票 {code} 的分析结果失败: {str(e)}")
        
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
        self.BATCH_SIZE = 50
        self.BATCH_DELAY = 1
        self.checkpoint_file = 'data/checkpoint.json'
        self.analysis_results = []
        self.stock_names = get_stock_name_dict()

    def analyze_stocks(self, stock_list, logger_manager=None):
        """分析多个股票"""
        try:
            logger = logger_manager.get_logger("analyze_stocks") if logger_manager else LoggerManager().get_logger("analyze_stocks")
            
            # 初始化统计信息
            start_time = time.time()
            success_count = 0
            error_count = 0
            cache_hit_count = 0
            results = []
            
            # 创建检查点文件
            checkpoint_file = f'data/checkpoint_{datetime.now().strftime("%Y%m%d")}.json'
            
            # 打印初始信息
            total_stocks = len(stock_list)
            print(f"\n{Fore.CYAN}开始分析 {total_stocks} 只股票...{Style.RESET_ALL}")
            print(Fore.GREEN + "=" * 50 + Style.RESET_ALL)
            
            # 创建进度条
            pbar = tqdm(total=total_stocks, 
                       desc=Fore.BLUE + "处理进度" + Style.RESET_ALL,
                       bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]")
            
            # 处理每个股票
            with Pool(processes=min(cpu_count(), 4)) as pool:
                process_args = [(stock, logger_manager, checkpoint_file) for stock in stock_list]
                
                for result in pool.imap_unordered(process_stock, process_args):
                    if result:
                        success_count += 1
                        if result.get('from_cache', False):
                            cache_hit_count += 1
                        results.append(result)
                    else:
                        error_count += 1
                    
                    # 更新进度条
                    pbar.update(1)
                    
                    # 更新进度条描述
                    pbar.set_postfix({
                        '成功': f"{Fore.GREEN}{success_count}{Style.RESET_ALL}",
                        '失败': f"{Fore.RED}{error_count}{Style.RESET_ALL}",
                        '缓存命中': cache_hit_count
                    }, refresh=True)
                    
                    # 每处理10只股票，打印详细统计
                    if (success_count + error_count) % 10 == 0:
                        elapsed_time = time.time() - start_time
                        avg_time = elapsed_time / (success_count + error_count)
                        
                        print(f"\n{Fore.YELLOW}{'-' * 50}")
                        print(f"""详细统计:
{Fore.CYAN}- 成功: {success_count}
{Fore.RED}- 失败: {error_count}
{Fore.GREEN}- 缓存命中: {cache_hit_count}
{Fore.BLUE}- 平均耗时: {avg_time:.1f}秒/股
{Fore.MAGENTA}- 缓存命中率: {(cache_hit_count/(success_count + error_count)*100) if (success_count + error_count) > 0 else 0:.1f}%{Style.RESET_ALL}
""")
                        print(f"{Fore.YELLOW}{'-' * 50}{Style.RESET_ALL}")
            
            # 关闭进度条
            pbar.close()
            
            # 最终统计
            total_time = time.time() - start_time
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
            
            return results
            
        except Exception as e:
            logger.error(f"分析股票失败: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def generate_summary_report(self):
        """生成汇总报告"""
        try:
            if not self.analysis_results:
                print("没有分析结果可供汇总")
                return
                
            print("\n开始生成汇总报告...")
            
            # 创建DataFrame
            df = pd.DataFrame(self.analysis_results)
            
            # 添加股票名称列
            df['name'] = df['code'].map(self.stock_names)
            
            # 调整列顺序，将code和name放在前面
            columns = ['code', 'name'] + [col for col in df.columns if col not in ['code', 'name']]
            df = df[columns]
            
            # 生成买入信号排序报告
            buy_signals_report = df[df['buy_signals'] > 0].sort_values(
                by=['buy_signals', 'sell_signals'], 
                ascending=[False, True]
            )
            
            # 生成卖出信号排序报告
            sell_signals_report = df[df['sell_signals'] > 0].sort_values(
                by=['sell_signals', 'buy_signals'], 
                ascending=[False, True]
            )
            
            # 保存汇总报告
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 保存买入信号报告
            if not buy_signals_report.empty:
                buy_report_file = f'summary/buy_signals_{current_time}.csv'
                buy_signals_report.to_csv(buy_report_file, index=False, encoding='utf-8-sig')
                print(f"\n买入信号汇总报告已保存到: {buy_report_file}")
                print("\n买入信号最多的前10只股票:")
                print(buy_signals_report[['code', 'name', 'buy_signals', 'sell_signals', 'strategies']].head(10).to_string())
            else:
                print("\n没有股票产生买入信号")
            
            # 保存卖出信号报告
            if not sell_signals_report.empty:
                sell_report_file = f'summary/sell_signals_{current_time}.csv'
                sell_signals_report.to_csv(sell_report_file, index=False, encoding='utf-8-sig')
                print(f"\n卖出信号汇总报告已保存到: {sell_report_file}")
                print("\n卖出信号最多的前10只股票:")
                print(sell_signals_report[['code', 'name', 'buy_signals', 'sell_signals', 'strategies']].head(10).to_string())
            else:
                print("\n没有股票产生卖出信号")
            
            # 生成统计摘要
            print("\n策略信号统计:")
            print(f"总分析股票数: {len(df)}")
            print(f"产生买入信号的股票数: {len(buy_signals_report)}")
            print(f"产生卖出信号的股票数: {len(sell_signals_report)}")
            
            # 保存完整的汇总数据
            summary_file = f'summary/full_analysis_{current_time}.json'
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
            print(f"\n完整分析汇总已保存到: {summary_file}")
            
        except Exception as e:
            error_msg = f"生成汇总报告失败: {str(e)}"
            print(error_msg)
            self.logger.error(error_msg)


