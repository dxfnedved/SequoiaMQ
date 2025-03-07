#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
import os
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import traceback
import concurrent.futures
import psutil
import gc
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入自定义模块
from data_loader import StockDataLoader
from model import StockLSTM
from lstm_with_thoughts import StockLSTMWithThoughts
from technical_analyzer import TechnicalAnalyzer
from logger_manager import LoggerManager

def predict_stock(stock_code_or_name, args, logger):
    """预测单只股票"""
    try:
        # 初始化技术分析器
        analyzer = TechnicalAnalyzer()
        
        # 获取纯净的股票代码
        stock_code = analyzer._get_pure_stock_code(stock_code_or_name)
        if not stock_code:
            logger.error(f"无法获取有效的股票代码: {stock_code_or_name}")
            return None
        
        logger.info(f"开始预测股票: {stock_code}")
        
        # 获取股票数据
        df_with_indicators, stock_name = get_stock_data_with_indicators(stock_code, args.start_date, args.end_date, logger)
        if df_with_indicators is None:
            logger.error(f"无法获取股票数据: {stock_code}")
            return None
            
        # 准备特征数据
        df_features = prepare_feature_data(df_with_indicators)
        feature_dims = len(df_features.columns)
        
        logger.info(f"使用 {feature_dims} 个特征进行预测: {', '.join(df_features.columns)}")
        
        # 根据选择的模型类型初始化模型
        if args.model_type == 'lstm':
            logger.info("使用标准LSTM模型")
            model = StockLSTM(time_step=args.time_step, feature_dims=feature_dims)
        else:
            logger.info("使用思维增强LSTM模型")
            model = StockLSTMWithThoughts(
                time_step=args.time_step,
                feature_dims=feature_dims,
                thought_dim=args.thought_dim,
                num_thoughts=args.num_thoughts,
                num_heads=args.num_heads
            )
            logger.info(f"模型配置: 思维维度={args.thought_dim}, 思维数量={args.num_thoughts}, 注意力头数={args.num_heads}")
        
        # 准备数据
        X_train, Y_train, X_test, Y_test = model.prepare_data(df_features.values)
        
        # 训练模型
        logger.info(f"开始训练模型: {stock_code}")
        model.train(X_train, Y_train, epochs=args.epochs, batch_size=args.batch_size)
        
        # 进行预测
        logger.info(f"生成预测结果: {stock_code}")
        train_predict = model.predict(X_train)
        test_predict = model.predict(X_test)
        
        # 预测未来价格
        logger.info(f"预测未来 {args.future_days} 天的价格: {stock_code}")
        future_predictions = predict_future_prices(model, df_features, days=args.future_days, feature_dims=feature_dims)
        
        # 评估模型
        metrics = model.evaluate(X_test, Y_test)
        logger.info(f"{stock_code} 模型评估指标：")
        logger.info(f"均方误差 (MSE): {metrics['MSE']:.4f}")
        logger.info(f"均方根误差 (RMSE): {metrics['RMSE']:.4f}")
        logger.info(f"平均绝对误差 (MAE): {metrics['MAE']:.4f}")
        logger.info(f"平均绝对百分比误差 (MAPE): {metrics['MAPE']:.4f}%")
        
        # 输出未来预测结果
        logger.info(f"\n{stock_code} 未来价格预测结果：")
        future_dates = [datetime.now() + timedelta(days=i+1) for i in range(args.future_days)]
        for i, (date, pred) in enumerate(zip(future_dates, future_predictions)):
            # 修复格式化错误，将numpy.ndarray转换为float
            # 处理多层嵌套的numpy数组
            if isinstance(pred, (list, np.ndarray)):
                if isinstance(pred[0], (list, np.ndarray)):
                    pred_value = float(pred[0][0])
                else:
                    pred_value = float(pred[0])
            else:
                pred_value = float(pred)
            logger.info(f"{date.strftime('%Y-%m-%d')}: {pred_value:.2f}")
        
        # 保存结果
        result_file = save_results(stock_code, stock_name, metrics, future_predictions, output_dir=args.output_dir)
        
        # 生成预测图表
        if not args.no_plot:
            try:
                logger.info(f"开始生成预测图表: {stock_code}")
                
                # 设置中文字体
                try:
                    import matplotlib as mpl
                    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
                    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                except Exception as e:
                    logger.warning(f"设置中文字体失败: {str(e)}")
                
                # 实际收盘价
                actual_data = df_features['close'].values
                
                # 获取日期索引
                try:
                    if hasattr(df_with_indicators, 'index') and len(df_with_indicators.index) > 0:
                        date_index = df_with_indicators.index[-len(actual_data):]
                    else:
                        date_index = pd.date_range(end=datetime.now(), periods=len(actual_data))
                except Exception as e:
                    logger.error(f"生成日期索引时出错: {str(e)}")
                    date_index = pd.date_range(end=datetime.now(), periods=len(actual_data))
                
                # 创建图表
                plt.figure(figsize=(14, 8))
                
                # 绘制实际股价
                plt.plot(date_index, actual_data, label='实际股价', alpha=0.6)
                
                # 训练集预测
                train_predict_plot = np.empty_like(actual_data)
                train_predict_plot[:] = np.nan
                train_end_idx = min(args.time_step + len(train_predict), len(train_predict_plot))
                train_predict_plot[args.time_step:train_end_idx] = train_predict.flatten()[:train_end_idx-args.time_step]
                plt.plot(date_index, train_predict_plot, label='训练集预测', alpha=0.8)
                
                # 测试集预测
                test_predict_plot = np.empty_like(actual_data)
                test_predict_plot[:] = np.nan
                test_start_idx = len(train_predict) + args.time_step
                test_end_idx = min(test_start_idx + len(test_predict), len(test_predict_plot))
                if test_end_idx > test_start_idx:
                    test_predict_plot[test_start_idx:test_end_idx] = test_predict.flatten()[:test_end_idx-test_start_idx]
                    plt.plot(date_index, test_predict_plot, label='测试集预测', alpha=0.8)
                
                # 未来预测
                last_date = date_index[-1]
                future_dates = [last_date + timedelta(days=i+1) for i in range(args.future_days)]
                # 调整未来日期，跳过周末
                for i in range(len(future_dates)):
                    while future_dates[i].weekday() >= 5:  # 5和6代表周六和周日
                        future_dates[i] += timedelta(days=1)
                
                # 处理预测值，确保正确转换numpy数组
                future_values = []
                for pred in future_predictions:
                    if isinstance(pred, (list, np.ndarray)):
                        if isinstance(pred[0], (list, np.ndarray)):
                            future_values.append(float(pred[0][0]))
                        else:
                            future_values.append(float(pred[0]))
                    else:
                        future_values.append(float(pred))
                
                plt.plot(future_dates, future_values, 'r--', label='未来预测', alpha=0.8)
                
                # 设置图表属性
                plt.gca().xaxis.set_major_formatter(mpl.dates.DateFormatter('%Y-%m-%d'))
                plt.gca().xaxis.set_major_locator(mpl.dates.MonthLocator(interval=2))
                plt.gcf().autofmt_xdate()  # 自动旋转日期标签
                
                plt.legend()
                plt.xlabel('交易日')
                plt.ylabel('股价')
                plt.title(f'{stock_code}({stock_name}) - {args.model_type.upper()} 股票价格预测')
                plt.grid(True, alpha=0.3)
                
                # 保存图表
                plot_dir = os.path.join(args.output_dir, 'plots')
                os.makedirs(plot_dir, exist_ok=True)
                plot_file = os.path.join(plot_dir, f"{stock_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                plt.savefig(plot_file)
                logger.info(f"预测图表已保存到: {plot_file}")
                
                # 关闭图表，释放内存
                plt.close()
                
            except Exception as e:
                logger.error(f"生成预测图表时出错: {str(e)}")
                logger.error(traceback.format_exc())
        
        return {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'metrics': metrics,
            'future_predictions': future_predictions,
            'result_file': result_file
        }
        
    except Exception as e:
        logger.error(f"预测股票 {stock_code_or_name} 时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def get_stock_data_with_indicators(code_or_name, start_date=None, end_date=None, logger=None):
    """获取股票数据并计算技术指标"""
    try:
        # 初始化技术分析器
        analyzer = TechnicalAnalyzer()
        
        # 获取纯净的股票代码
        stock_code = analyzer._get_pure_stock_code(code_or_name)
        if not stock_code:
            if logger:
                logger.error(f"无法获取有效的股票代码: {code_or_name}")
            return None, None
        
        # 初始化数据加载器
        data_loader = StockDataLoader()
        
        # 获取股票名称
        stock_name = data_loader.get_stock_name(stock_code)
        
        # 直接使用akshare获取股票数据
        try:
            import akshare as ak
            
            # 如果未指定日期，默认获取近两年数据
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=730)).strftime('%Y%m%d')
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
                
            # 获取股票数据
            try:
                # 尝试使用stock_zh_a_hist函数
                df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"
                )
                if df is None or df.empty:
                    raise Exception("获取数据为空")
            except Exception as e1:
                try:
                    # 尝试使用stock_zh_a_daily函数
                    market = "sh" if stock_code.startswith(("6", "9")) else "sz"
                    df = ak.stock_zh_a_daily(
                        symbol=f"{market}{stock_code}",
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq"
                    )
                    if df is None or df.empty:
                        raise Exception("获取数据为空")
                except Exception as e2:
                    if logger:
                        logger.error(f"获取股票数据失败: {str(e1)}, {str(e2)}")
                    return None, None
            
            # 标准化列名
            column_map = {
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'pct_change',
                '涨跌额': 'change',
                '换手率': 'turnover'
            }
            
            # 重命名存在的列
            rename_dict = {k: v for k, v in column_map.items() if k in df.columns}
            if rename_dict:
                df = df.rename(columns=rename_dict)
            
            # 设置日期索引
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
            
            # 计算技术指标
            df_with_indicators = analyzer.calculate_all_indicators(df)
            
            return df_with_indicators, stock_name
            
        except Exception as e:
            if logger:
                logger.error(f"获取股票数据时出错: {str(e)}")
            return None, None
            
    except Exception as e:
        if logger:
            logger.error(f"获取股票数据时出错: {str(e)}")
        return None, None

def prepare_feature_data(df):
    """准备特征数据"""
    try:
        # 选择要使用的特征
        feature_columns = [
            'close',  # 收盘价
            'MA5', 'MA10', 'MA20',  # 移动平均线
            'RSI6', 'RSI12',  # RSI指标
            'MACD', 'MACD_Signal',  # MACD指标
            'BOLL_UPPER', 'BOLL_MIDDLE', 'BOLL_LOWER',  # 布林带
            'ATR'  # 平均真实范围
        ]
        
        # 确保所有特征列都存在
        available_features = [col for col in feature_columns if col in df.columns]
        
        # 如果某些特征不存在，使用基本特征
        if len(available_features) < 5:
            # 使用基本的OHLCV数据
            basic_features = ['close']
            for col in ['open', 'high', 'low', 'volume']:
                if col in df.columns:
                    basic_features.append(col)
            
            # 计算简单的技术指标
            if 'close' in df.columns:
                # 计算简单移动平均线
                for period in [5, 10, 20]:
                    col_name = f'MA{period}'
                    df[col_name] = df['close'].rolling(window=period).mean()
                    basic_features.append(col_name)
                
                # 计算价格变化率
                df['price_change'] = df['close'].pct_change()
                basic_features.append('price_change')
                
                # 计算波动率
                df['volatility'] = df['price_change'].rolling(window=20).std()
                basic_features.append('volatility')
            
            available_features = [col for col in basic_features if col in df.columns]
        
        # 选择特征并删除NaN值
        df_features = df[available_features].copy()
        df_features.dropna(inplace=True)
        
        return df_features
        
    except Exception as e:
        print(f"准备特征数据时出错: {str(e)}")
        # 返回最基本的特征
        return df[['close']].dropna()

def predict_future_prices(model, df_features, days=7, feature_dims=None):
    """预测未来价格"""
    try:
        # 获取最近的数据作为预测的起点
        last_sequence = df_features.values[-model.time_step:].copy()
        
        # 如果未指定特征维度，使用数据的列数
        if feature_dims is None:
            feature_dims = df_features.shape[1]
        
        # 预测未来几天的价格
        future_predictions = []
        
        for _ in range(days):
            # 准备输入数据
            X_pred = last_sequence.reshape(1, model.time_step, feature_dims)
            
            # 预测下一天的价格
            pred = model.predict(X_pred)
            future_predictions.append(pred)
            
            # 更新序列，移除最早的一天，添加预测的一天
            # 注意：我们只更新收盘价（第一列），其他特征保持不变
            new_day = last_sequence[-1].copy()
            new_day[0] = pred[0][0]  # 更新收盘价
            
            last_sequence = np.vstack([last_sequence[1:], new_day])
        
        return future_predictions
    
    except Exception as e:
        print(f"预测未来价格时出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []

def save_results(stock_code, stock_name, metrics, predictions, output_dir='results'):
    """保存分析结果"""
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 处理预测结果，确保可以JSON序列化
        processed_predictions = []
        for pred in predictions:
            if isinstance(pred, (list, np.ndarray)):
                if isinstance(pred[0], (list, np.ndarray)):
                    processed_predictions.append(float(pred[0][0]))
                else:
                    processed_predictions.append(float(pred[0]))
            else:
                processed_predictions.append(float(pred))
        
        # 准备结果数据
        result = {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': {
                'MAE': float(metrics['MAE']),
                'MAPE': float(metrics['MAPE'])
            },
            'future_predictions': processed_predictions,
            'last_prediction': float(processed_predictions[-1]) if processed_predictions and len(processed_predictions) > 0 else None
        }
        
        # 生成输出文件名
        result_file = os.path.join(output_dir, f"{stock_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # 保存结果
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
            
        print(f"\n分析结果已保存到: {result_file}")
        return result_file
    except Exception as e:
        print(f"保存结果时出错: {e}")
        return None

class BatchPredictor:
    def __init__(self, logger, results_dir, predictor):
        self.logger = logger
        self.results_dir = results_dir
        self.predictor = predictor  # 股票预测器实例

    def batch_predict(self, stock_codes, num_workers=4, memory_limit_percent=75, gc_interval=10):
        """
        批量预测多只股票
        
        参数:
            stock_codes (list): 股票代码列表
            num_workers (int): 并行处理的工作线程数
            memory_limit_percent (int): 内存使用限制百分比，超过此值时暂停处理
            gc_interval (int): 垃圾回收间隔（处理多少只股票后进行一次gc）
            
        返回:
            list: 预测结果列表
        """
        results = []
        total_stocks = len(stock_codes)
        self.logger.info(f"开始批量预测，共 {total_stocks} 只股票，使用 {num_workers} 个工作线程")
        
        # 自动调整线程数，根据CPU核心数
        available_cores = os.cpu_count() or 4
        if num_workers > available_cores:
            self.logger.info(f"调整工作线程数为CPU核心数: {available_cores}")
            num_workers = available_cores
        
        # 创建结果目录
        os.makedirs(self.results_dir, exist_ok=True)
        
        # 批量预测状态记录
        status_file = os.path.join(self.results_dir, "batch_status.json")
        status = {
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_stocks": total_stocks,
            "completed": 0,
            "successful": 0,
            "failed": 0,
            "in_progress": False
        }
        
        # 检查是否有未完成的批处理
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    prev_status = json.load(f)
                
                if prev_status.get('in_progress', False):
                    self.logger.warning("发现未完成的批处理任务，将从上次中断的位置继续")
                    completed_codes = prev_status.get('completed_codes', [])
                    stock_codes = [code for code in stock_codes if code not in completed_codes]
                    status['completed'] = prev_status.get('completed', 0)
                    status['successful'] = prev_status.get('successful', 0)
                    status['failed'] = prev_status.get('failed', 0)
            except Exception as e:
                self.logger.error(f"读取批处理状态文件出错: {str(e)}")
        
        # 更新批处理状态
        status['in_progress'] = True
        status['completed_codes'] = []
        self._save_status(status_file, status)
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = {}
                
                for i, code in enumerate(stock_codes):
                    # 检查内存使用情况
                    if i > 0 and i % gc_interval == 0:
                        gc.collect()  # 强制垃圾回收
                        
                    mem_usage = psutil.virtual_memory().percent
                    if mem_usage > memory_limit_percent:
                        self.logger.warning(f"内存使用率达到 {mem_usage}%，暂停处理并等待内存释放")
                        # 等待正在进行的任务完成
                        while futures and mem_usage > memory_limit_percent - 10:
                            time.sleep(5)
                            mem_usage = psutil.virtual_memory().percent
                            self.logger.info(f"当前内存使用率: {mem_usage}%，等待降低...")
                            
                            # 检查完成的任务
                            done_futures = []
                            for future_code, future in futures.items():
                                if future.done():
                                    done_futures.append(future_code)
                            
                            # 处理完成的任务结果
                            for future_code in done_futures:
                                future = futures.pop(future_code)
                                try:
                                    result = future.result()
                                    self._process_result(result, status, status_file)
                                except Exception as e:
                                    self.logger.error(f"处理股票 {future_code} 预测结果时出错: {str(e)}")
                                    status['failed'] += 1
                    
                    # 提交预测任务
                    self.logger.info(f"提交预测任务 [{i+1}/{total_stocks}]: {code}")
                    future = executor.submit(self._predict_single_stock, code)
                    futures[code] = future
                    
                    # 定期检查完成的任务
                    if i > 0 and i % 10 == 0 or i == len(stock_codes) - 1:
                        completed = []
                        for future_code, future in futures.items():
                            if future.done():
                                completed.append(future_code)
                        
                        for future_code in completed:
                            future = futures.pop(future_code)
                            try:
                                result = future.result()
                                self._process_result(result, status, status_file)
                                results.append(result)
                            except Exception as e:
                                self.logger.error(f"处理股票 {future_code} 预测结果时出错: {str(e)}")
                                status['failed'] += 1
                        
                        # 更新状态文件
                        self._save_status(status_file, status)
                
                # 等待所有任务完成
                for code, future in futures.items():
                    try:
                        result = future.result()
                        self._process_result(result, status, status_file)
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"处理股票 {code} 预测结果时出错: {str(e)}")
                        status['failed'] += 1
        
        except Exception as e:
            self.logger.error(f"批量预测过程中出错: {str(e)}")
            self.logger.error(traceback.format_exc())
        
        finally:
            # 更新批处理状态
            status['in_progress'] = False
            status['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._save_status(status_file, status)
            
            self.logger.info(f"批量预测完成，共处理 {status['completed']} 只股票，"
                            f"成功 {status['successful']} 只，失败 {status['failed']} 只")
        
        return results
    
    def _predict_single_stock(self, stock_code):
        """处理单只股票预测"""
        try:
            result = self.predictor.predict_stock(stock_code)
            return {'code': stock_code, 'success': True, 'data': result}
        except Exception as e:
            self.logger.error(f"预测股票 {stock_code} 时出错: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {'code': stock_code, 'success': False, 'error': str(e)}
    
    def _process_result(self, result, status, status_file):
        """处理预测结果并更新状态"""
        if result['success']:
            status['successful'] += 1
        else:
            status['failed'] += 1
        
        status['completed'] += 1
        status['completed_codes'].append(result['code'])
    
    def _save_status(self, status_file, status):
        """保存批处理状态"""
        try:
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.logger.error(f"保存批处理状态文件出错: {str(e)}")

def get_stocks_from_watchlist(watchlist_path="watchlist.json"):
    """从自选股列表获取股票代码"""
    try:
        if not os.path.exists(watchlist_path):
            return []
        
        with open(watchlist_path, 'r', encoding='utf-8') as f:
            watchlist = json.load(f)
        
        # 提取股票代码
        if isinstance(watchlist, list):
            stock_codes = [item.get('code') for item in watchlist if item.get('code')]
        elif isinstance(watchlist, dict) and 'stocks' in watchlist:
            stock_codes = [item.get('code') for item in watchlist['stocks'] if item.get('code')]
        else:
            stock_codes = []
        
        return stock_codes
    except Exception as e:
        print(f"读取自选股列表出错: {str(e)}")
        return []

def get_all_stock_codes():
    """获取所有A股股票代码"""
    try:
        # 导入数据获取模块
        from stock_cache import StockCache
        from logger_manager import LoggerManager
        
        # 初始化日志
        logger_manager = LoggerManager()
        logger = logger_manager.get_logger("get_all_stocks")
        
        # 初始化股票缓存
        stock_cache = StockCache(logger_manager=logger_manager)
        
        # 获取所有股票信息
        all_stocks = stock_cache.get_all_stock_info()
        
        # 过滤出A股股票代码
        stock_codes = []
        for code, info in all_stocks.items():
            # 排除ST股票、退市股票、科创板和北交所
            if (not info.get('name', '').startswith('*') and  # 排除ST
                not info.get('name', '').lower().startswith('st') and
                not code.startswith('688') and  # 排除科创板
                not code.startswith('4') and  # 排除北交所
                info.get('exchange') in ['SH', 'SZ'] and  # 只保留沪深交易所
                info.get('status') != 'D'):  # 排除退市
                stock_codes.append(code)
        
        logger.info(f"获取到 {len(stock_codes)} 只A股股票")
        return stock_codes
    except Exception as e:
        print(f"获取所有股票代码时出错: {str(e)}")
        return []

def main():
    parser = argparse.ArgumentParser(description='A股LSTM股票批量预测分析工具')
    parser.add_argument('--stocks', type=str, help='股票代码列表，多个代码用逗号分隔')
    parser.add_argument('--watchlist', action='store_true', help='使用自选股列表')
    parser.add_argument('--all-stocks', action='store_true', help='分析所有A股股票')
    parser.add_argument('--limit', type=int, default=0, help='限制分析的股票数量')
    parser.add_argument('--output-dir', type=str, default='LSTM/results', help='结果输出目录')
    parser.add_argument('--threads', type=int, default=4, help='并行线程数')
    parser.add_argument('--memory-limit', type=int, default=75, help='内存使用限制百分比')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='日志级别')
    args = parser.parse_args()
    
    # 设置日志级别
    logger_manager = LoggerManager()
    logger = logger_manager.get_logger("lstm_batch_predict")
    
    log_level = getattr(logging, args.log_level)
    logger.setLevel(log_level)
    
    start_time = time.time()
    logger.info("开始批量预测分析...")
    
    try:
        # 确保输出目录存在
        os.makedirs(args.output_dir, exist_ok=True)
        
        # 获取股票代码列表
        stock_codes = []
        
        if args.stocks:
            stock_codes = args.stocks.split(',')
            logger.info(f"使用指定的股票列表: {stock_codes}")
        elif args.watchlist:
            logger.info("使用自选股列表")
            stock_codes = get_stocks_from_watchlist()
        elif args.all_stocks:
            logger.info("获取所有A股股票列表")
            stock_codes = get_all_stock_codes()
        else:
            logger.error("未指定股票列表，请使用 --stocks, --watchlist 或 --all-stocks 参数")
            return
        
        if not stock_codes:
            logger.error("未获取到有效的股票列表")
            return
        
        logger.info(f"共获取到 {len(stock_codes)} 只股票")
        
        # 应用限制
        if args.limit > 0 and args.limit < len(stock_codes):
            logger.info(f"限制分析数量为 {args.limit} 只股票")
            stock_codes = stock_codes[:args.limit]
        
        # 初始化预测器
        from LSTM.predict import StockPredictor
        predictor = StockPredictor(logger_manager=logger_manager)
        
        # 初始化批量预测器
        batch_predictor = BatchPredictor(
            logger=logger,
            results_dir=args.output_dir,
            predictor=predictor
        )
        
        # 开始批量预测
        results = batch_predictor.batch_predict(
            stock_codes=stock_codes,
            num_workers=args.threads,
            memory_limit_percent=args.memory_limit
        )
        
        # 处理预测结果
        successful = [r for r in results if r.get('success', False)]
        
        logger.info(f"预测完成，成功率: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.2f}%)")
        
        # 汇总结果
        summary_file = os.path.join(args.output_dir, f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total': len(results),
                    'successful': len(successful),
                    'failed': len(results) - len(successful),
                    'duration': time.time() - start_time,
                    'detailed_results': [
                        {
                            'code': r.get('code'),
                            'success': r.get('success', False),
                            'error': r.get('error') if not r.get('success', False) else None
                        } for r in results
                    ]
                }, f, ensure_ascii=False, indent=4)
            logger.info(f"结果汇总已保存到 {summary_file}")
        except Exception as e:
            logger.error(f"保存结果汇总时出错: {str(e)}")
        
    except Exception as e:
        logger.error(f"批量预测过程中出错: {str(e)}")
        logger.error(traceback.format_exc())
    
    finally:
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"批量预测分析完成，总耗时: {duration:.2f} 秒")

if __name__ == "__main__":
    main() 