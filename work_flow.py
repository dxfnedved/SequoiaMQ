# -*- encoding: UTF-8 -*-

import os
import json
import pandas as pd
from datetime import datetime
from data_fetcher import DataFetcher
from strategy_analyzer import StrategyAnalyzer
from logger_manager import LoggerManager
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import traceback
from tqdm import tqdm
from colorama import init, Fore, Style
import utils
from settings import ANALYSIS_CACHE_DIR,SUMMARY_DIR

# 初始化colorama，确保在Windows上也能正常显示颜色
init(autoreset=True)

def process_stock_data(args):
    """处理单个股票数据的线程函数"""
    stock, logger_manager, batch_id = args
    logger = logger_manager.get_logger("process_stock")
    
    try:
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
            
        # 分析数据
        start_time = time.time()
        result = strategy_analyzer.analyze_stock(code)
        analysis_time = time.time() - start_time
        
        if result and 'strategy_results' in result:
            # 预处理结果
            processed_result = {
                'code': code,
                'name': name,
                'buy_signals': 0,
                'sell_signals': 0,
                'strategies': [],
                'signal_details': [],
                'data_date': result.get('last_date', ''),
                'analysis_time': analysis_time,
                'batch_id': batch_id
            }
            
            # 统计买入卖出信号
            for strategy_name, strategy_result in result['strategy_results'].items():
                if isinstance(strategy_result, dict) and 'signal' in strategy_result:
                    signal = strategy_result['signal']
                    if signal == '买入':
                        processed_result['buy_signals'] += 1
                        processed_result['strategies'].append(f"{strategy_name}(买入)")
                        processed_result['signal_details'].append({
                            'strategy': strategy_name,
                            'type': '买入',
                            'factors': strategy_result.get('factors', {}),
                            'strength': strategy_result.get('buy_strength', 1),
                            'execution_time': strategy_result.get('execution_time', 0)
                        })
                    elif signal == '卖出':
                        processed_result['sell_signals'] += 1
                        processed_result['strategies'].append(f"{strategy_name}(卖出)")
                        processed_result['signal_details'].append({
                            'strategy': strategy_name,
                            'type': '卖出',
                            'factors': strategy_result.get('factors', {}),
                            'strength': strategy_result.get('sell_strength', 1),
                            'execution_time': strategy_result.get('execution_time', 0)
                        })
            
            # 添加技术指标数据
            if 'indicators' in result:
                processed_result['indicators'] = result['indicators']
            
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
        self.summary_dir = SUMMARY_DIR

        # 性能优化参数
        self.max_workers = min(64, (os.cpu_count() or 1) * 8)  # 线程数
        self.batch_size = 200  # 批处理大小
        
        # 缓存和断点相关
        self.cache_dir = ANALYSIS_CACHE_DIR
        self.checkpoint_file = os.path.join(self.cache_dir, 'checkpoint.json')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 性能统计
        self.performance_stats = {
            'total_time': 0,
            'success_count': 0,
            'error_count': 0,
            'cache_hit_count': 0,
            'avg_time_per_stock': 0,
            'batch_times': [],
            'strategy_times': {}
        }

    def _save_checkpoint(self, processed_stocks, results):
        """保存分析检查点"""
        try:
            checkpoint_data = {
                'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'processed_stocks': processed_stocks,
                'results': results,
                'performance_stats': self.performance_stats
            }
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"保存检查点成功: {len(processed_stocks)} 只股票")
        except Exception as e:
            self.logger.error(f"保存检查点失败: {str(e)}")

    def _load_checkpoint(self):
        """加载分析检查点"""
        try:
            if os.path.exists(self.checkpoint_file):
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                    
                # 检查检查点时效性（24小时）
                if 'timestamp' not in checkpoint_data:
                    self.logger.info("检查点数据格式无效，将重新开始分析")
                    return [], []
                    
                checkpoint_time = datetime.strptime(checkpoint_data['timestamp'], '%Y%m%d_%H%M%S')
                if (datetime.now() - checkpoint_time).total_seconds() > 24 * 60 * 60:
                    self.logger.info("检查点已过期，将重新开始分析")
                    return [], []
                
                # 加载性能统计
                if 'performance_stats' in checkpoint_data:
                    self.performance_stats = checkpoint_data['performance_stats']
                    
                self.logger.info(f"加载检查点成功: {len(checkpoint_data['processed_stocks'])} 只股票")
                return checkpoint_data['processed_stocks'], checkpoint_data['results']
            return [], []
        except Exception as e:
            self.logger.error(f"加载检查点失败: {str(e)}")
            return [], []

    def generate_summary_report(self):
        """生成分析汇总报告"""
        try:
            if not self.analysis_results:
                self.logger.warning("没有分析结果可供生成报告")
                return False

            # 创建报告目录
            report_dir = 'summary'
            os.makedirs(report_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 生成报告文件名
            report_file = os.path.join(report_dir, f'analysis_report_{timestamp}.json')
            excel_file = os.path.join(report_dir, f'analysis_report_{timestamp}.xlsx')
            performance_file = os.path.join(report_dir, f'performance_report_{timestamp}.json')
            
            # 统计信息
            total_stocks = len(self.analysis_results)
            buy_signals = sum(1 for r in self.analysis_results if r and r.get('buy_signals', 0) > 0)
            sell_signals = sum(1 for r in self.analysis_results if r and r.get('sell_signals', 0) > 0)
            
            # 创建汇总数据
            summary = {
                'timestamp': timestamp,
                'total_stocks': total_stocks,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'results': self.analysis_results
            }
            
            # 保存JSON格式报告
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
                
            # 创建Excel格式报告
            df_data = []
            for result in self.analysis_results:
                if result:
                    row = {
                        '股票代码': result.get('code', ''),
                        '股票名称': result.get('name', ''),
                        '买入信号数': result.get('buy_signals', 0),
                        '卖出信号数': result.get('sell_signals', 0),
                        '触发策略': ','.join(result.get('strategies', [])),
                        '数据日期': result.get('data_date', ''),
                        '来源': '缓存' if result.get('from_cache', False) else '实时',
                        '分析耗时(秒)': round(result.get('analysis_time', 0), 2)
                    }
                    
                    # 添加技术指标
                    if 'indicators' in result:
                        for indicator, value in result['indicators'].items():
                            if value is not None:
                                row[f'指标_{indicator}'] = round(value, 2)
                    
                    df_data.append(row)
                    
            # 保存Excel报告
            if df_data:
                df = pd.DataFrame(df_data)
                df.to_excel(excel_file, index=False)
            
            # 保存性能报告
            with open(performance_file, 'w', encoding='utf-8') as f:
                json.dump(self.performance_stats, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"生成分析报告成功: {report_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"生成分析报告失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def analyze_stocks(self, stock_list):
        """分析股票列表"""
        try:
            # 获取当前有效的股票代码集合
            current_stock_codes = {stock['code'] for stock in stock_list}
            
            # 加载检查点，但只保留当前有效的股票的结果
            processed_stocks, checkpoint_results = self._load_checkpoint()
            valid_processed_stocks = []
            valid_results = []
            
            if processed_stocks and checkpoint_results:
                # 检查检查点中的结果是否仍然有效
                for stock_code, result in zip(processed_stocks, checkpoint_results):
                    if stock_code in current_stock_codes:
                        # 检查结果的时效性（确保结果不超过24小时）
                        if 'timestamp' not in result:
                            continue
                        try:
                            result_time = datetime.strptime(result['timestamp'], '%Y-%m-%d %H:%M:%S')
                            if (datetime.now() - result_time).total_seconds() <= 24 * 60 * 60:
                                valid_processed_stocks.append(stock_code)
                                valid_results.append(result)
                            else:
                                self.logger.info(f"股票 {stock_code} 的分析结果已过期，将重新分析")
                        except (ValueError, TypeError):
                            self.logger.warning(f"股票 {stock_code} 的时间戳格式无效，将重新分析")
                            continue
                    
                if len(valid_processed_stocks) != len(processed_stocks):
                    removed_count = len(processed_stocks) - len(valid_processed_stocks)
                    self.logger.info(f"从检查点中移除了 {removed_count} 只无效或过期的股票")
                    
                if valid_processed_stocks:
                    self.logger.info(f"从检查点恢复 {len(valid_processed_stocks)} 只有效股票的分析结果")
                    self.analysis_results = valid_results
                    processed_stocks = valid_processed_stocks
                else:
                    self.logger.info("检查点中没有有效的股票结果，将重新开始分析")
                    processed_stocks = []
                    self.analysis_results = []
            
            # 过滤掉已处理的股票
            remaining_stocks = [stock for stock in stock_list if stock['code'] not in set(processed_stocks)]
            
            if not remaining_stocks:
                self.logger.info("所有股票已经处理完毕，无需重新分析")
                return True
                
            # 执行新闻分析（全局一次）
            self.strategy_analyzer.perform_news_analysis()
                
            # 分批处理剩余股票
            total_remaining = len(remaining_stocks)
            self.logger.info(f"开始分析 {total_remaining} 只股票...")
            
            # 初始化进度条
            progress_bar = tqdm(total=total_remaining, desc="分析进度", unit="只")
            
            # 记录开始时间
            start_time = time.time()
            
            # 分批处理
            batch_count = (total_remaining + self.batch_size - 1) // self.batch_size
            success_count = 0
            error_count = 0
            cache_hit_count = 0
            
            for batch_idx in range(batch_count):
                batch_start = batch_idx * self.batch_size
                batch_end = min(batch_start + self.batch_size, total_remaining)
                batch = remaining_stocks[batch_start:batch_end]
                
                batch_start_time = time.time()
                self.logger.info(f"处理批次 {batch_idx + 1}/{batch_count}，包含 {len(batch)} 只股票")
                
                # 并行处理批次
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # 提交任务
                    futures = [
                        executor.submit(process_stock_data, (stock, self.logger_manager, batch_idx))
                        for stock in batch
                    ]
                    
                    # 处理结果
                    batch_results = []
                    for future in as_completed(futures):
                        try:
                            result = future.result()
                            if result:
                                batch_results.append(result)
                                success_count += 1
                                
                                # 检查是否来自缓存
                                if result.get('from_cache', False):
                                    cache_hit_count += 1
                                    
                                # 更新策略执行时间统计
                                for signal_detail in result.get('signal_details', []):
                                    strategy_name = signal_detail.get('strategy', 'unknown')
                                    exec_time = signal_detail.get('execution_time', 0)
                                    
                                    if strategy_name not in self.performance_stats['strategy_times']:
                                        self.performance_stats['strategy_times'][strategy_name] = {
                                            'total_time': 0,
                                            'count': 0,
                                            'avg_time': 0
                                        }
                                        
                                    stats = self.performance_stats['strategy_times'][strategy_name]
                                    stats['total_time'] += exec_time
                                    stats['count'] += 1
                                    stats['avg_time'] = stats['total_time'] / stats['count']
                            else:
                                error_count += 1
                                
                            # 更新进度条
                            progress_bar.update(1)
                            
                        except Exception as e:
                            self.logger.error(f"处理批次结果时出错: {str(e)}")
                            error_count += 1
                            progress_bar.update(1)
                
                # 批次处理完成
                batch_time = time.time() - batch_start_time
                self.performance_stats['batch_times'].append({
                    'batch_id': batch_idx,
                    'size': len(batch),
                    'time': batch_time,
                    'avg_time_per_stock': batch_time / len(batch) if batch else 0
                })
                
                # 更新分析结果
                self.analysis_results.extend(batch_results)
                
                # 更新已处理股票列表
                for stock in batch:
                    processed_stocks.append(stock['code'])
                    
                # 每批次保存一次检查点
                self._save_checkpoint(processed_stocks, self.analysis_results)
                
                # 打印批次统计信息
                self._print_statistics(success_count, error_count, cache_hit_count, 
                                      batch_time / len(batch) if batch else 0)
            
            # 关闭进度条
            progress_bar.close()
            
            # 计算总耗时
            total_time = time.time() - start_time
            self.performance_stats['total_time'] = total_time
            self.performance_stats['success_count'] = success_count
            self.performance_stats['error_count'] = error_count
            self.performance_stats['cache_hit_count'] = cache_hit_count
            self.performance_stats['avg_time_per_stock'] = total_time / total_remaining if total_remaining else 0
            
            # 打印最终统计信息
            self._print_final_statistics(total_remaining, success_count, error_count, 
                                        cache_hit_count, total_time)
            
            # 保存最终检查点
            self._save_checkpoint(processed_stocks, self.analysis_results)
            
            return True
            
        except Exception as e:
            self.logger.error(f"分析股票列表时出错: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def _print_statistics(self, success_count, error_count, cache_hit_count, avg_time):
        """打印统计信息"""
        print(f"\n{Fore.CYAN}当前统计:{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}成功:{Style.RESET_ALL} {success_count} 只")
        print(f"  {Fore.RED}失败:{Style.RESET_ALL} {error_count} 只")
        print(f"  {Fore.YELLOW}缓存命中:{Style.RESET_ALL} {cache_hit_count} 只")
        print(f"  {Fore.BLUE}平均耗时:{Style.RESET_ALL} {avg_time:.2f} 秒/只")
        
    def _print_final_statistics(self, total_stocks, success_count, error_count,
                              cache_hit_count, total_time):
        """打印最终统计信息"""
        print(f"\n{Fore.CYAN}分析完成，最终统计:{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}总计:{Style.RESET_ALL} {total_stocks} 只")
        print(f"  {Fore.GREEN}成功:{Style.RESET_ALL} {success_count} 只 ({success_count/total_stocks*100:.1f}%)")
        print(f"  {Fore.RED}失败:{Style.RESET_ALL} {error_count} 只 ({error_count/total_stocks*100:.1f}%)")
        print(f"  {Fore.YELLOW}缓存命中:{Style.RESET_ALL} {cache_hit_count} 只 ({cache_hit_count/total_stocks*100:.1f}%)")
        print(f"  {Fore.BLUE}总耗时:{Style.RESET_ALL} {total_time:.2f} 秒")
        print(f"  {Fore.BLUE}平均耗时:{Style.RESET_ALL} {total_time/total_stocks:.2f} 秒/只")
        
        # 打印策略执行时间统计
        if self.performance_stats['strategy_times']:
            print(f"\n{Fore.CYAN}策略执行时间统计:{Style.RESET_ALL}")
            sorted_strategies = sorted(
                self.performance_stats['strategy_times'].items(),
                key=lambda x: x[1]['avg_time'],
                reverse=True
            )
            for strategy_name, stats in sorted_strategies:
                print(f"  {Fore.WHITE}{strategy_name}:{Style.RESET_ALL} {stats['avg_time']:.4f} 秒/次 (执行 {stats['count']} 次)")

    def prepare(self):
        """准备工作流程"""
        try:
            self.logger.info("开始准备工作流程...")
            
            # 获取股票列表
            stock_list = self.data_fetcher.get_stock_list()
            if not stock_list:
                self.logger.error("获取股票列表失败")
                return False
                
            # 分析股票
            self.logger.info(f"开始分析 {len(stock_list)} 只股票...")
            success = self.analyze_stocks(stock_list)
            
            if not success:
                self.logger.error("分析股票失败")
                return False
                
            # 生成报告
            self.logger.info("生成分析报告...")
            if not self.generate_summary_report():
                self.logger.error("生成分析报告失败")
                return False
                
            self.logger.info("工作流程执行完成")
            return True
            
        except Exception as e:
            self.logger.error(f"准备工作流程时出错: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False
            
    def save_analysis_results(self, stock_code, results):
        """保存分析结果到缓存"""
        try:
            # 确保缓存目录存在
            os.makedirs(self.cache_dir, exist_ok=True)
            
            # 生成缓存文件路径
            cache_file = os.path.join(self.cache_dir, f"{stock_code}_analysis.json")
            
            # 保存结果
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                
            self.logger.debug(f"保存分析结果到缓存: {stock_code}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存分析结果到缓存失败 {stock_code}: {str(e)}")
            return False
            
    def process_stock_data(self, stock_code):
        """处理单个股票数据"""
        try:
            # 获取股票名称
            stock_name = self.stock_names.get(stock_code, "未知")
            
            # 分析股票
            result = self.strategy_analyzer.analyze_stock(stock_code)
            
            if result:
                # 处理结果
                processed_result = {
                    'code': stock_code,
                    'name': stock_name,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'strategy_results': result.get('strategy_results', {}),
                    'last_price': result.get('last_price'),
                    'last_volume': result.get('last_volume'),
                    'last_date': result.get('last_date')
                }
                
                # 保存结果到缓存
                self.save_analysis_results(stock_code, processed_result)
                
                return processed_result
                
            return None
            
        except Exception as e:
            self.logger.error(f"处理股票 {stock_code} 数据时出错: {str(e)}")
            return None


