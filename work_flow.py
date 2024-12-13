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

def get_stock_name_dict():
    """获取股票代码到名称的映射字典"""
    stock_list = get_stock_list()
    return {code: name for code, name in stock_list}

def process_stock(args):
    """处理单个股票的静态方法（用于多进程）"""
    stock, logger_manager, checkpoint_file = args
    try:
        data_fetcher = DataFetcher(logger_manager=logger_manager)
        strategy_analyzer = StrategyAnalyzer(logger_manager=logger_manager)
        
        code = stock['code'] if isinstance(stock, dict) else stock
        
        # 检查是否已处理过
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, 'r') as f:
                processed_stocks = json.load(f)
            if code in processed_stocks:
                return None
        
        # 检查缓存
        cache_file = f'cache/stock_data_{code}.pkl'
        if os.path.exists(cache_file):
            try:
                data = pd.read_pickle(cache_file)
                # 检查数据是否需要更新（如果最后一天不是今天）
                if data.index[-1].date() != datetime.now().date():
                    data = data_fetcher.get_stock_data(code)
                    if data is not None and not data.empty:
                        data.to_pickle(cache_file)
            except Exception:
                # 如果读取缓存失败，直接获取新数据
                data = data_fetcher.get_stock_data(code)
                if data is not None and not data.empty:
                    data.to_pickle(cache_file)
        else:
            data = data_fetcher.get_stock_data(code)
            if data is not None and not data.empty:
                data.to_pickle(cache_file)
        
        if data is None or data.empty:
            return None
            
        # 分析数据
        result = strategy_analyzer.analyze(data, code)
        
        if result:
            # 预处理结果
            processed_result = {'code': code, 'buy_signals': 0, 'sell_signals': 0, 'strategies': []}
            
            # 统计买入卖出信号
            for strategy_name, strategy_result in result.items():
                if isinstance(strategy_result, dict) and 'signal' in strategy_result:
                    if strategy_result['signal'] == '买入':
                        processed_result['buy_signals'] += 1
                        processed_result['strategies'].append(f"{strategy_name}(买入)")
                    elif strategy_result['signal'] == '卖出':
                        processed_result['sell_signals'] += 1
                        processed_result['strategies'].append(f"{strategy_name}(卖出)")
            
            processed_result['analysis_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 保存分析结果
            result_file = f'data/analysis_{code}_{datetime.now().strftime("%Y%m%d")}.json'
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(processed_result, f, indent=2, ensure_ascii=False)
            
            # 更新检查点
            if os.path.exists(checkpoint_file):
                with open(checkpoint_file, 'r') as f:
                    processed_stocks = json.load(f)
            else:
                processed_stocks = []
            
            processed_stocks.append(code)
            with open(checkpoint_file, 'w') as f:
                json.dump(processed_stocks, f)
            
            return processed_result
        
        return None
        
    except Exception as e:
        print(f"分析股票{code}时出错: {str(e)}")
        return None

class WorkFlow:
    """工作流程类"""
    def __init__(self, logger_manager=None):
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("work_flow")
        
        # 初始化数据获取器和策略分析器
        self.data_fetcher = DataFetcher(logger_manager=self.logger_manager)
        self.strategy_analyzer = StrategyAnalyzer(logger_manager=self.logger_manager)
        
        # 用于存储所有分析结果
        self.analysis_results = []
        
        # 设置批处理参数
        self.BATCH_SIZE = 50
        self.BATCH_DELAY = 5  # 批次间延迟（秒）
        
        # 获取股票名称字典
        self.stock_names = get_stock_name_dict()
        
        # 检查点文件
        self.checkpoint_file = 'data/checkpoint.json'

    def prepare(self):
        """准备工作"""
        try:
            print("开始准备工作...")
            self.logger.info("开始准备工作")
            
            # 创建必要的目录
            for dir_name in ['data', 'logs', 'cache', 'summary']:
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)
                    print(f"创建目录: {dir_name}")
                    
            # 判断运行模式
            is_gui_mode = len(sys.argv) > 1 and sys.argv[1] == '--gui'
            
            if is_gui_mode:
                # GUI模式下使用自选股列表
                watchlist_file = 'data/watchlist.json'
                if os.path.exists(watchlist_file):
                    with open(watchlist_file, 'r', encoding='utf-8') as f:
                        stock_list = json.load(f)
                    print(f"加载自选股列表: {len(stock_list)}只股票")
                else:
                    print("未找到自选股列表，将分析所有A股")
                    stock_list = self.data_fetcher.get_stock_list()
            else:
                # 命令行模式下分析全量股票
                print("命令行模式：分析全量A股")
                stock_list = self.data_fetcher.get_stock_list()
                print(f"获取到 {len(stock_list)} 只A股")
                
            # 开始分析
            self.analyze_stocks(stock_list)
            
            # 生成汇总报告
            self.generate_summary_report()
            
        except Exception as e:
            error_msg = f"准备工作失败: {str(e)}"
            print(error_msg)
            self.logger.error(error_msg)

    def analyze_stocks(self, stock_list):
        """分析股票（使用多进程）"""
        try:
            total = len(stock_list)
            print(f"\n开始分析{total}只股票...")
            start_time = time.time()
            
            # 确定进程数（使用CPU核心数的2倍，因为涉及I/O操作）
            num_processes = min(cpu_count() * 2, 8)  # 最多使用8个进程，避免过多并发请求
            print(f"使用{num_processes}个进程进行并行处理")
            
            # 将股票列表分成多个批次
            batches = [stock_list[i:i + self.BATCH_SIZE] for i in range(0, len(stock_list), self.BATCH_SIZE)]
            
            # 准备进程参数
            process_args = [(stock, self.logger_manager, self.checkpoint_file) for batch in batches for stock in batch]
            
            # 使用进程池处理
            results = []
            for batch_idx, batch in enumerate(batches):
                print(f"\n处理第 {batch_idx + 1}/{len(batches)} 批...")
                
                with Pool(num_processes) as pool:
                    batch_args = [(stock, self.logger_manager, self.checkpoint_file) for stock in batch]
                    batch_results = []
                    for i, result in enumerate(pool.imap_unordered(process_stock, batch_args), 1):
                        if result:
                            batch_results.append(result)
                        progress = min((batch_idx * self.BATCH_SIZE + i) / total * 100, 100)
                        print(f"\r处理进度: {progress:.1f}% ({batch_idx * self.BATCH_SIZE + i}/{total})", end='', flush=True)
                
                results.extend(batch_results)
                
                # 批次间延迟
                if batch_idx < len(batches) - 1:
                    print(f"\n等待 {self.BATCH_DELAY} 秒后处理下一批...")
                    time.sleep(self.BATCH_DELAY)
            
            print("\n")  # 换行
            
            # 更新分析结果
            self.analysis_results = [r for r in results if r is not None]
            
            end_time = time.time()
            duration = end_time - start_time
            print(f"\n分析完成! 总用时: {duration:.2f}秒")
            print(f"成功分析: {len(self.analysis_results)}/{total} 只股票")
            
        except Exception as e:
            error_msg = f"分析股票失败: {str(e)}"
            print(error_msg)
            self.logger.error(error_msg)

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


