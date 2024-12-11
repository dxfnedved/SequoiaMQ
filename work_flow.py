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
    BacktraceMA250Strategy,
    CompositeStrategy
)
from logger_manager import LoggerManager
import traceback
from tqdm import tqdm
import concurrent.futures

class WorkFlow:
    def __init__(self):
        # 初始化日志管理器
        self.logger_manager = LoggerManager()
        self.logger = self.logger_manager.get_logger("work_flow", propagate=False)
        
        # 初始化所有策略
        self.strategies = [
            CompositeStrategy(self.logger_manager),
            Alpha101Strategy(self.logger_manager),
            Alpha191Strategy(self.logger_manager),
            RSRS_Strategy(self.logger_manager),
            TurtleStrategy(self.logger_manager),
            EnterStrategy(self.logger_manager),
            LowATRStrategy(self.logger_manager),
            LowBacktraceIncreaseStrategy(self.logger_manager),
            KeepIncreasingStrategy(self.logger_manager),
            BacktraceMA250Strategy(self.logger_manager)
        ]
        
        # 初始化数据获取器
        self.data_fetcher = data_fetcher.DataFetcher(self.logger_manager)
        
        # 创建结果目录
        self.setup_result_dirs()
        
    def setup_result_dirs(self):
        """设置结果目录"""
        # 基础结果目录
        self.results_dir = os.path.join('results', 'analysis')
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            
        # 当日结果目录（使用固定的日期目录）
        self.today = datetime.now().strftime('%Y%m%d')
        self.today_dir = os.path.join(self.results_dir, self.today)
        if not os.path.exists(self.today_dir):
            os.makedirs(self.today_dir)
            
    def analyze_single_stock(self, code_name_tuple):
        """分析单个股票"""
        code, name = code_name_tuple
        try:
            # 获取数据
            data = self.data_fetcher.fetch_stock_data(code)
            if data is None or len(data) < 60:  # 确保有足够的数据
                self.logger.debug(f"获取股票 {code} {name} 数据失败或数据不足")
                return None
                
            # 执行策略分析
            stock_result = {
                '股票代码': code,
                '股票名称': name,
                '分析时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '收盘价': data['收盘'].iloc[-1] if not data.empty else None
            }
            
            # 记录各策略信号
            all_signals = []
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
                            all_signals.extend(strategy_signals)
                            stock_result[f'{strategy_name}_信号'] = [s['type'] for s in strategy_signals]
                            
                except Exception as e:
                    self.logger.debug(f"策略 {strategy.__class__.__name__} 分析股票 {code} 失败: {str(e)}")
                    continue
                    
            # 合并信号到结果中
            if all_signals:
                stock_result['signals'] = all_signals
                
            return stock_result
            
        except Exception as e:
            self.logger.error(f"分析股票 {code} 失败: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return None
            
    def prepare(self):
        """准备分析任务"""
        try:
            # 获取股票列表
            stock_list = utils.get_stock_list()
            if not stock_list:
                self.logger.error("获取股票列表失败")
                return
                
            total_stocks = len(stock_list)
            self.logger.info(f"开始分析 {total_stocks} 只股票")
            
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
                completed = 0
                
                for future in concurrent.futures.as_completed(future_to_stock):
                    stock = future_to_stock[future]
                    completed += 1
                    
                    # 每处理5%的股票更新一次进度
                    if completed % max(1, total_stocks // 20) == 0:
                        progress = (completed / total_stocks) * 100
                        self.logger.info(f"分析进度: {progress:.1f}% ({completed}/{total_stocks})")
                    
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                            # 只在发现信号时记录
                            if any(s.get('signal') == '买入' for s in result.get('signals', [])):
                                self.logger.info(f"发现买入信号: {result['股票代码']} {result['股票名称']}")
                            elif any(s.get('signal') == '卖出' for s in result.get('signals', [])):
                                self.logger.info(f"发现卖出信号: {result['股票代码']} {result['股票名称']}")
                    except Exception as e:
                        self.logger.error(f"处理股票 {stock[0]} 结果失败: {str(e)}")
                        
            # 保存结果
            if results:
                self.save_results(results)
                self.logger.info(f"分析完成，共处理 {total_stocks} 只股票，产生 {len(results)} 个结果")
                
        except Exception as e:
            self.logger.error(f"准备分析任务失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            
    def save_results(self, results):
        """保存分析结果"""
        try:
            # 使用固定的结果目录
            current_time = datetime.now().strftime('%H%M%S')
            
            # 重新组织结果数据
            analysis_results = []
            signal_results = []
            trend_results = []
            
            for result in results:
                if not isinstance(result, dict):
                    continue
                    
                # 基本信息
                stock_info = {
                    '股票代码': result.get('股票代码'),
                    '股票名称': result.get('股票名称'),
                    '分析时间': result.get('分析时间'),
                    '收盘价': result.get('收盘价')
                }
                
                # 处理策略结果
                stock_signals = []  # 收集所有策略的信号
                stock_trends = {}   # 收集所有策略的趋势指标
                
                for strategy in self.strategies:
                    strategy_name = strategy.__class__.__name__
                    strategy_result = result.get(f'{strategy_name}_结果')
                    
                    if not strategy_result or not isinstance(strategy_result, dict):
                        continue
                        
                    # 收集趋势指标
                    if 'trend' in strategy_result:
                        stock_trends['MACD趋势'] = strategy_result['trend']
                        
                    if 'bb_position' in strategy_result:
                        stock_trends['布林带位置'] = strategy_result['bb_position']
                    elif all(k in strategy_result for k in ['upper', 'lower']):
                        upper = strategy_result['upper']
                        lower = strategy_result['lower']
                        middle = strategy_result.get('middle', (upper + lower) / 2)
                        stock_trends['布林带上轨'] = upper
                        stock_trends['布林带中轨'] = middle
                        stock_trends['布林带下轨'] = lower
                        
                    if 'rsi' in strategy_result:
                        stock_trends['RSI'] = strategy_result['rsi']
                        
                    if 'atr' in strategy_result:
                        stock_trends['ATR'] = strategy_result['atr']
                    elif 'atr_ratio' in strategy_result:
                        stock_trends['ATR比率'] = strategy_result['atr_ratio']
                        
                    # 其他技术指标
                    for ma in ['ma5', 'ma10', 'ma20', 'ma60']:
                        if ma in strategy_result:
                            stock_trends[ma.upper()] = strategy_result[ma]
                            
                    # 形态识别结果
                    for pattern in ['platform_breakthrough', 'high_tight_flag', 'parking_apron']:
                        if pattern in strategy_result:
                            stock_trends[pattern] = strategy_result[pattern]
                            
                    # 收集信号
                    if strategy_result.get('signal') and strategy_result['signal'] != '无':
                        signal_info = {
                            '策略名称': strategy_name,
                            '信号类型': strategy_result.get('signal', '无'),
                            '建议止损': strategy_result.get('initial_stop', '未设置'),
                            '跟踪止损': strategy_result.get('trailing_stop', '未设置')
                        }
                        stock_signals.append(signal_info)
                
                # 生成趋势分析记录
                if stock_trends:
                    trend_info = {**stock_info, **stock_trends}
                    trend_results.append(trend_info)
                
                # 生成信号记录
                for signal in stock_signals:
                    signal_info = {
                        **stock_info,
                        **signal,
                        **{k: v for k, v in stock_trends.items() if k in ['MACD趋势', 'RSI', 'ATR']}
                    }
                    signal_results.append(signal_info)
                
                # 生成详细分析记录
                analysis_info = {
                    **stock_info,
                    **stock_trends,
                    '信号数量': len(stock_signals),
                    '信号详情': '; '.join([f"{s['策略名称']}: {s['信号类型']}" for s in stock_signals]) if stock_signals else '无信号'
                }
                analysis_results.append(analysis_info)
            
            # 保存趋势分析结果
            if trend_results:
                trend_df = pd.DataFrame(trend_results)
                trend_file = os.path.join(self.today_dir, f'trend_analysis_{current_time}.csv')
                trend_df.to_csv(trend_file, index=False, encoding='utf-8-sig')
                self.logger.info(f"趋势分析结果已保存到: {trend_file}")
            
            # 保存信号结果
            if signal_results:
                signal_df = pd.DataFrame(signal_results)
                signal_file = os.path.join(self.today_dir, f'trading_signals_{current_time}.csv')
                signal_df.to_csv(signal_file, index=False, encoding='utf-8-sig')
                self.logger.info(f"交易信号已保存到: {signal_file}")
            
            # 保存详细分析结果
            if analysis_results:
                analysis_df = pd.DataFrame(analysis_results)
                analysis_file = os.path.join(self.today_dir, f'detailed_analysis_{current_time}.csv')
                analysis_df.to_csv(analysis_file, index=False, encoding='utf-8-sig')
                self.logger.info(f"详细分析结果已保存到: {analysis_file}")
            
            # 生成结果摘要
            summary = {
                '分析时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '分析股票数': len(results),
                '产生信号数': len(signal_results),
                '上升趋势数': sum(1 for r in trend_results if r.get('MACD趋势') == 1),
                '下降趋势数': sum(1 for r in trend_results if r.get('MACD趋势') == -1),
                '强势股数量': sum(1 for r in trend_results if r.get('RSI', 0) > 70),
                '弱势股数量': sum(1 for r in trend_results if r.get('RSI', 0) < 30)
            }
            
            summary_df = pd.DataFrame([summary])
            summary_file = os.path.join(self.today_dir, f'analysis_summary_{current_time}.csv')
            summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
            self.logger.info(f"分析摘要已保存到: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"保存结果失败: {str(e)}")
            self.logger.error(traceback.format_exc())


