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
from settings import ANALYSIS_CACHE_DIR

# 初始化colorama，确保在Windows上也能正常显示颜色
init(autoreset=True)

def process_stock_data(args):
    """处理单个股票数据的线程函数"""
    stock, logger_manager = args
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
        result = strategy_analyzer.analyze_stock(code)
        
        if result and 'strategy_results' in result:
            # 预处理结果
            processed_result = {
                'code': code,
                'name': name,
                'buy_signals': 0,
                'sell_signals': 0,
                'strategies': [],
                'signal_details': [],
                'data_date': result.get('last_date', '')
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
                            'strength': strategy_result.get('buy_strength', 1)
                        })
                    elif signal == '卖出':
                        processed_result['sell_signals'] += 1
                        processed_result['strategies'].append(f"{strategy_name}(卖出)")
                        processed_result['signal_details'].append({
                            'strategy': strategy_name,
                            'type': '卖出',
                            'factors': strategy_result.get('factors', {}),
                            'strength': strategy_result.get('sell_strength', 1)
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
        self.max_workers = min(64, (os.cpu_count() or 1) * 8)  # 线程数
        self.batch_size = 200  # 批处理大小
        
        # 缓存和断点相关
        self.cache_dir = ANALYSIS_CACHE_DIR
        self.checkpoint_file = os.path.join(self.cache_dir, 'checkpoint.json')
        os.makedirs(self.cache_dir, exist_ok=True)

    def _save_checkpoint(self, processed_stocks, results):
        """保存分析检查点"""
        try:
            checkpoint_data = {
                'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'processed_stocks': processed_stocks,
                'results': results
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
            
            # 统计信息
            total_stocks = len(self.analysis_results)
            buy_signals = sum(1 for r in self.analysis_results if r and r.get('buy_signals', 0) > 0)
            sell_signals = sum(1 for r in self.analysis_results if r and r.get('sell_signals', 0) > 0)
            
            # 创建��总数据
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
                        '来源': '缓存' if result.get('from_cache', False) else '实时'
                    }
                    df_data.append(row)
                    
            # 保存Excel报告
            if df_data:
                df = pd.DataFrame(df_data)
                df.to_excel(excel_file, index=False)
                
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
                    self.logger.info("检查点中没有有效的股票结果，将重新开始��析")
                    processed_stocks = []
                    self.analysis_results = []
            
            # 过滤掉已处理的股票
            remaining_stocks = [stock for stock in stock_list if stock['code'] not in set(processed_stocks)]
            
            if not remaining_stocks:
                self.logger.info("所有股票都已分析完成")
                return self.analysis_results
                
            total_stocks = len(remaining_stocks)
            self.logger.info(f"开始分析剩余的 {total_stocks} 只股票")
            
            # 初始化统计信息
            start_time = time.time()
            success_count = len(valid_results)
            error_count = 0
            cache_hit_count = sum(1 for r in valid_results if r.get('from_cache', False))
            
            # 创建进度条
            progress_bar = tqdm(
                total=total_stocks,
                desc=f"{Fore.BLUE}分析进度{Style.RESET_ALL}",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
                ncols=100,
                unit="只",
                initial=len(valid_results)
            )
            
            # 使用线程池处理
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_stock = {
                    executor.submit(process_stock_data, (stock, self.logger_manager)): stock 
                    for stock in remaining_stocks
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
                            self.analysis_results.append(result)
                            processed_stocks.append(stock['code'])
                        else:
                            error_count += 1
                            
                        # 更新进度条
                        progress_bar.update(1)
                        progress_bar.set_postfix({
                            '成功': f"{Fore.GREEN}{success_count}{Style.RESET_ALL}",
                            '失败': f"{Fore.RED}{error_count}{Style.RESET_ALL}",
                            '缓存': cache_hit_count
                        }, refresh=True)
                        
                        # 每处理10只股票保存一次检查点
                        if (success_count + error_count) % 50 == 0:
                            self._save_checkpoint(processed_stocks, self.analysis_results)
                            
                        # 定期显示统计信息
                        if (success_count + error_count) % 5000 == 0:
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
            
            # 保存最终检查点
            self._save_checkpoint(processed_stocks, self.analysis_results)
            
            # 打印最终统计信息
            total_time = time.time() - start_time
            self._print_final_statistics(total_stocks, success_count, error_count,
                                      cache_hit_count, total_time)
            
            return self.analysis_results
            
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

    def prepare(self):
        """准备工作流程，包括数据获取和分析"""
        try:
            self.logger.info("开始准备工作流程...")
            
            # 获取所有A股列表
            stock_list = self.data_fetcher.get_stock_list()
            if not stock_list:
                self.logger.error("获取股票列表失败")
                return False
                
            self.logger.info(f"获取到 {len(stock_list)} 只股票")
            
            # 执行全局新闻分析（只执行一次）
            if not self.strategy_analyzer.perform_news_analysis():
                self.logger.warning("全局新闻分析未能完成，将继续执行其他策略")
            
            # 分析股票
            results = self.analyze_stocks(stock_list)
            if not results:
                self.logger.error("分析股票失败")
                return False
                
            # 生成分析报告
            if not self.generate_summary_report():
                self.logger.error("生成分析报告失败")
                return False
                
            self.logger.info("工作流程准备完成")
            return True
            
        except Exception as e:
            self.logger.error(f"工作流程准备失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def save_analysis_results(self, stock_code, results):
        """保存分析结果"""
        try:
            # 保存常规分析结果
            if results.get('signals'):
                signals_df = pd.DataFrame(results['signals'])
                signals_df.to_excel(
                    os.path.join(self.summary_dir, f'{stock_code}_signals.xlsx'),
                    index=False
                )
                
            # 保存新闻分析结果
            news_signals = [s for s in results.get('signals', []) 
                           if s.get('strategy') == 'NewsStrategy']
            if news_signals:
                news_df = pd.DataFrame(news_signals)
                # 确保summary_dir存在
                os.makedirs(self.summary_dir, exist_ok=True)
                # 保存到单独的新闻分析表格
                news_file = os.path.join(self.summary_dir, f'{stock_code}_news_analysis.xlsx')
                news_df.to_excel(news_file, index=False)
                self.logger.info(f"新闻分析结果已保存到: {news_file}")
                
        except Exception as e:
            self.logger.error(f"保存分析结果失败: {str(e)}")
            
    def process_stock_data(self, stock_code):
        """处理单个股票数据"""
        try:
            # 获取股票数据
            data = self.data_fetcher.get_stock_data(stock_code)
            if data is None:
                return None
            
            # 初始化结果字典
            results = {'signals': []}
            
            # 运行所有策略
            for strategy in self.strategies:
                try:
                    signals = strategy.get_signals(data)
                    if signals:
                        results['signals'].extend(signals)
                except Exception as e:
                    self.logger.error(f"策略 {strategy.name} 分析失败: {str(e)}")
                    continue
                    
            # 保存分析结果
            if results['signals']:
                self.save_analysis_results(stock_code, results)
                
            return results
            
        except Exception as e:
            self.logger.error(f"处理股票 {stock_code} 数据失败: {str(e)}")
            return None


