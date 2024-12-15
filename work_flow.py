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
import random
import utils  # 添加utils模块导入

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
        
        logger.info(f"开始处理股票: {code} ({name})")
        
        # 检查是否已处理过
        if os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, 'r') as f:
                    processed_stocks = json.load(f)
                if code in processed_stocks:
                    logger.info(f"股票 {code} 已处理过，跳过")
                    return None
            except Exception as e:
                logger.error(f"读取检查点文件失败: {str(e)}")
                processed_stocks = []
        else:
            processed_stocks = []
        
        # 获取数据
        data = data_fetcher.get_stock_data(stock)
        if data is None:
            logger.error(f"股票 {code} 数据获取失败")
            return None
            
        if data.empty:
            logger.error(f"股票 {code} 数据为空")
            return None
            
        # 记录数据来源
        from_cache = data_fetcher.is_from_cache(code)
        logger.info(f"股票 {code} 数据来源: {'缓存' if from_cache else '实时获取'}")
        
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
                        
                    logger.info(f"股票 {code} 分析完成，发现 {processed_result['buy_signals']} 个买入信号，{processed_result['sell_signals']} 个卖出信号")
                    return processed_result
                    
                except Exception as e:
                    logger.error(f"保存股票 {code} 的分析结果失败: {str(e)}")
            else:
                logger.info(f"股票 {code} 没有产生买入或卖出信号")
        else:
            logger.info(f"股票 {code} 分析结果为空")
        
        return None
        
    except Exception as e:
        logger.error(f"处理股票 {code} 时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return None

class WorkFlow:
    """工作流程类"""
    def __init__(self, logger_manager=None):
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("workflow")
        
        # 初始化组件
        self.data_fetcher = DataFetcher(logger_manager=self.logger_manager)
        self.strategy_analyzer = StrategyAnalyzer(logger_manager=self.logger_manager)
        
        # 批处理配置
        self.BATCH_SIZE = 50  # 每批处理的股票数量
        self.BATCH_DELAY = 1  # 批次间延迟（秒）
        
        # 检查点文件
        self.checkpoint_file = 'data/checkpoint.json'
        
        # 分析结果
        self.analysis_results = []
        
        # 获取股票名称字典
        self.stock_names = get_stock_name_dict()

    def prepare(self):
        """准备工作"""
        try:
            print("开始准备工作...")
            self.logger.info("开始准备工作")
            
            # 创建必要的目录
            for dir_name in ['data', 'logs', 'cache', 'summary']:
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)
                    self.logger.info(f"创建目录: {dir_name}")
                    
            # 检查是否是开盘时间
            is_market_open = utils.is_market_open()
            market_status = utils.get_market_status()
            self.logger.info(f"当前市场状态: {market_status['message']}")
            
            # 判断运行模式
            is_gui_mode = len(sys.argv) > 1 and sys.argv[1] == '--gui'
            
            if is_gui_mode:
                # GUI模式下使用自选股列表
                watchlist_file = 'data/watchlist.json'
                if os.path.exists(watchlist_file):
                    with open(watchlist_file, 'r', encoding='utf-8') as f:
                        stock_list = json.load(f)
                    self.logger.info(f"加载自选股列表: {len(stock_list)}只股票")
                else:
                    self.logger.info("��找到自选股列表，将分析所有A股")
                    stock_list = utils.get_stock_list()
            else:
                # 命令行模式下分析全量股票
                self.logger.info("命令行模式：分析全量A股")
                stock_list = utils.get_stock_list()
                self.logger.info(f"获取到 {len(stock_list)} 只有效A股")
                
            # 开始分析
            self.analyze_stocks(stock_list)
            
            # 生成汇总报告
            self.generate_summary_report()
            
        except Exception as e:
            error_msg = f"准备工作失败: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())

    def analyze_stocks(self, stock_list):
        """分析股票（使用多进程）"""
        try:
            total = len(stock_list)
            self.logger.info(f"\n开始分析{total}只股票...")
            start_time = time.time()
            
            # 检查市场状态和缓存情况
            is_market_open = self.data_fetcher.is_market_open()
            cache_dir = self.data_fetcher.cache_dir
            cache_status = "需要更新" if is_market_open else "可以使用缓存"
            self.logger.info(f"市场状态: {'开盘' if is_market_open else '休市'}, 缓存状态: {cache_status}")
            
            # 确定进程数（根据市场状态调整）
            num_processes = min(cpu_count(), 4 if is_market_open else 8)
            self.logger.info(f"使用{num_processes}个进程进行并行处理")
            
            # 调整批处理参数
            batch_size = min(self.BATCH_SIZE, 20 if is_market_open else 50)
            self.logger.info(f"每批处理 {batch_size} 只股票")
            
            # 将股票列表分成多个批次
            batches = [stock_list[i:i + batch_size] for i in range(0, len(stock_list), batch_size)]
            
            # 统计信息初始化
            processed_count = 0
            success_count = 0
            error_count = 0
            cache_hit_count = 0
            cache_miss_count = 0
            signal_counts = {'买入': 0, '卖出': 0}
            all_results = []
            failed_stocks = []
            
            # 使用进程池处理
            for batch_idx, batch in enumerate(batches):
                self.logger.info(f"\n处理第 {batch_idx + 1}/{len(batches)} 批...")
                
                with Pool(num_processes) as pool:
                    batch_args = [(stock, self.logger_manager, self.checkpoint_file) for stock in batch]
                    batch_results = []
                    
                    # 处理当前批次
                    for idx, result in enumerate(pool.imap_unordered(process_stock, batch_args)):
                        processed_count += 1
                        
                        if result:
                            success_count += 1
                            batch_results.append(result)
                            # 统计信号
                            if result.get('buy_signals', 0) > 0:
                                signal_counts['买入'] += 1
                            if result.get('sell_signals', 0) > 0:
                                signal_counts['卖出'] += 1
                            # 统计缓存使用情况
                            if result.get('from_cache', False):
                                cache_hit_count += 1
                            else:
                                cache_miss_count += 1
                        else:
                            error_count += 1
                            stock = batch[idx]
                            failed_stocks.append(stock)
                        
                        # 输出进度
                        progress = min(processed_count / total * 100, 100)
                        self.logger.info(
                            f"\r进度: {progress:.1f}% ({processed_count}/{total}) "
                            f"成功: {success_count} 失败: {error_count} "
                            f"缓存命中: {cache_hit_count} 缓存未命中: {cache_miss_count} "
                            f"买入信号: {signal_counts['买入']} 卖出信号: {signal_counts['卖出']}"
                        )
                    
                    # 将批次结果添加到总结果列表
                    all_results.extend(batch_results)
                
                # 批次间延迟（根据市场状态调整）
                if batch_idx < len(batches) - 1:
                    if is_market_open:
                        delay = self.BATCH_DELAY + random.uniform(1, 2)  # 开盘时增加延迟
                    else:
                        delay = self.BATCH_DELAY + random.uniform(0.2, 0.5)  # 休市时减少延迟
                    self.logger.info(f"\n等待 {delay:.1f} 秒后处理下一批...")
                    time.sleep(delay)
            
            # 保存失败的股票列表
            if failed_stocks:
                failed_file = f'data/failed_stocks_{datetime.now().strftime("%Y%m%d")}.json'
                with open(failed_file, 'w', encoding='utf-8') as f:
                    json.dump(failed_stocks, f, indent=2, ensure_ascii=False)
                self.logger.info(f"\n失败的股票已保存到: {failed_file}")
            
            # 计算总用时
            end_time = time.time()
            duration = end_time - start_time
            
            # 输出最终统计信息
            self.logger.info(f"""
分析完成! 
总用时: {duration:.2f}秒
处理结果:
- 总股票数: {total}
- 成功处理: {success_count}
- 处理失败: {error_count}
- 缓存命中率: {(cache_hit_count/processed_count*100):.1f}%
- 买入信号: {signal_counts['买入']}
- 卖出信号: {signal_counts['卖出']}
- 平均处理时间: {duration/total:.2f}秒/只
            """)
            
            # 更新分析结果
            self.analysis_results = [r for r in all_results if r is not None]
            
        except Exception as e:
            error_msg = f"分析股票失败: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())

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


