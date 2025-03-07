#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
import os
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入自定义模块
from data_loader import StockDataLoader
from model import StockLSTM
from lstm_with_thoughts import StockLSTMWithThoughts
from technical_analyzer import TechnicalAnalyzer
from logger_manager import LoggerManager

def save_results(stock_code, stock_name, metrics, predictions, output_dir='results'):
    """保存分析结果"""
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 准备结果数据
        result = {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': metrics,
            'last_prediction': float(predictions[-1][0]) if predictions is not None and len(predictions) > 0 else None
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
            else:
                print(f"无法获取有效的股票代码: {code_or_name}")
            return None, None
        
        if logger:
            logger.info(f"获取到纯净的股票代码: {stock_code}")
        else:
            print(f"获取到纯净的股票代码: {stock_code}")
        
        # 初始化数据加载器
        data_loader = StockDataLoader()
        
        # 获取股票名称
        stock_name = data_loader.get_stock_name(stock_code)
        if logger:
            logger.info(f"获取到股票名称: {stock_name}")
        else:
            print(f"获取到股票名称: {stock_name}")
        
        # 直接使用akshare获取股票数据
        try:
            if logger:
                logger.info(f"尝试直接使用akshare获取股票数据: {stock_code}")
            else:
                print(f"尝试直接使用akshare获取股票数据: {stock_code}")
                
            import akshare as ak
            
            # 如果未指定日期，默认获取近两年数据
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=730)).strftime('%Y%m%d')
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
                
            if logger:
                logger.info(f"获取日期范围: {start_date} 到 {end_date}")
            else:
                print(f"获取日期范围: {start_date} 到 {end_date}")
            
            # 获取股票数据
            logger.info(f"使用akshare获取股票数据: {stock_code}")
            try:
                # 尝试使用stock_zh_a_hist函数
                logger.info("尝试使用stock_zh_a_hist函数获取数据...")
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
                logger.warning(f"使用stock_zh_a_hist获取数据失败: {str(e1)}")
                try:
                    # 尝试使用stock_zh_a_daily函数
                    logger.info("尝试使用stock_zh_a_daily函数获取数据...")
                    # 判断股票市场
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
                    logger.warning(f"使用stock_zh_a_daily获取数据失败: {str(e2)}")
                    try:
                        # 尝试使用stock_zh_a_hist_min_em函数
                        logger.info("尝试使用stock_zh_a_hist_min_em函数获取数据...")
                        df = ak.stock_zh_a_hist_min_em(
                            symbol=stock_code,
                            start_date=start_date.replace('-', ''),
                            end_date=end_date.replace('-', ''),
                            period='daily',
                            adjust='qfq'
                        )
                        if df is None or df.empty:
                            raise Exception("获取数据为空")
                    except Exception as e3:
                        logger.error(f"所有尝试都失败: {str(e1)}, {str(e2)}, {str(e3)}")
                        
                        # 最后尝试使用baostock获取数据
                        logger.info("尝试使用baostock获取数据...")
                        try:
                            # 不要在这里重新导入pandas，使用全局导入的pd
                            
                            # 登录系统
                            lg = bs.login()
                            if lg.error_code != '0':
                                logger.error(f"baostock登录失败: {lg.error_msg}")
                                raise Exception("baostock登录失败")
                                
                            # 获取股票数据
                            rs = bs.query_history_k_data_plus(
                                code=f"{'sh' if stock_code.startswith(('6', '9')) else 'sz'}.{stock_code}",
                                fields="date,open,high,low,close,volume,amount",
                                start_date=start_date.replace('-', ''),
                                end_date=end_date.replace('-', ''),
                                frequency="d",
                                adjustflag="2"  # 前复权
                            )
                            if rs.error_code != '0':
                                logger.error(f"baostock获取数据失败: {rs.error_msg}")
                                raise Exception("baostock获取数据失败")
                                
                            # 处理数据
                            data_list = []
                            while (rs.next()):
                                data_list.append(rs.get_row_data())
                            
                            # 登出系统
                            bs.logout()
                            
                            # 转换为DataFrame
                            df = pd.DataFrame(data_list, columns=rs.fields)
                            
                            # 转换数据类型
                            for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
                                if col in df.columns:
                                    df[col] = pd.to_numeric(df[col])
                                    
                            # 设置日期列
                            df['date'] = pd.to_datetime(df['date'])
                            
                            if df is None or df.empty:
                                raise Exception("baostock获取数据为空")
                                
                            logger.info("成功使用baostock获取数据")
                            
                        except Exception as e4:
                            logger.error(f"使用baostock获取数据失败: {str(e4)}")
                            raise Exception(f"无法获取股票数据: {stock_code}")
            
            if df is None or df.empty:
                if logger:
                    logger.error(f"akshare返回的数据为空: {stock_code}")
                else:
                    print(f"akshare返回的数据为空: {stock_code}")
                return None, None
            
            if logger:
                logger.info(f"成功获取到股票数据，共 {len(df)} 条记录")
            else:
                print(f"成功获取到股票数据，共 {len(df)} 条记录")
            
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
            logger.error(f"使用akshare获取数据失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # 不要直接退出，而是尝试使用get_stock_data_with_indicators函数获取数据
            logger.info("尝试使用get_stock_data_with_indicators函数获取数据...")
            df_with_indicators, stock_name = get_stock_data_with_indicators(stock_code, start_date, end_date, logger)
            if df_with_indicators is None:
                logger.error("无法获取股票数据，程序退出")
                sys.exit(1)
            logger.info(f"成功获取到股票数据，共 {len(df_with_indicators)} 条记录")
            
            # 使用获取到的数据继续处理
            df = df_with_indicators
        
        # 准备特征数据
        df_features = prepare_feature_data(df)
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
        logger.info("开始训练模型...")
        model.train(X_train, Y_train, epochs=args.epochs, batch_size=args.batch_size)
        
        # 进行预测
        logger.info("生成预测结果...")
        train_predict = model.predict(X_train)
        test_predict = model.predict(X_test)
        
        # 预测未来价格
        logger.info(f"预测未来 {args.future_days} 天的价格...")
        future_predictions = predict_future_prices(model, df_features, days=args.future_days, feature_dims=feature_dims)
        
        # 评估模型
        metrics = model.evaluate(X_test, Y_test)
        logger.info("模型评估指标：")
        logger.info(f"均方误差 (MSE): {metrics['MSE']:.4f}")
        logger.info(f"均方根误差 (RMSE): {metrics['RMSE']:.4f}")
        logger.info(f"平均绝对误差 (MAE): {metrics['MAE']:.4f}")
        logger.info(f"平均绝对百分比误差 (MAPE): {metrics['MAPE']:.4f}%")
        
        # 输出未来预测结果
        logger.info("\n未来价格预测结果：")
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
        save_results(stock_code, stock_name, metrics, future_predictions)
        
        # 显示预测图表
        if not args.no_plot:
            try:
                logger.info("开始生成预测图表...")
                # 绘制历史数据和预测结果
                plt.figure(figsize=(14, 8))
                
                # 设置中文字体
                try:
                    import matplotlib as mpl
                    # 尝试设置中文字体
                    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
                    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                    logger.info("成功设置中文字体")
                except Exception as e:
                    logger.warning(f"设置中文字体失败: {str(e)}")
                    # 使用英文标题
                    stock_name = f"{stock_code}"
                
                # 实际收盘价
                actual_data = df_features['close'].values
                logger.info(f"实际数据长度: {len(actual_data)}")
                
                # 获取日期索引
                try:
                    if hasattr(df, 'index') and len(df.index) > 0:
                        logger.info(f"使用DataFrame索引作为日期索引，索引长度: {len(df.index)}")
                        # 确保日期索引长度与数据长度匹配
                        if len(df.index) >= len(actual_data):
                            date_index = df.index[-len(actual_data):]
                            logger.info(f"使用DataFrame索引的后 {len(actual_data)} 个元素")
                        else:
                            logger.warning(f"DataFrame索引长度({len(df.index)})小于数据长度({len(actual_data)})，将生成新的日期索引")
                            date_index = pd.date_range(end=datetime.now(), periods=len(actual_data))
                    else:
                        logger.warning("DataFrame没有索引或索引为空，将生成新的日期索引")
                        date_index = pd.date_range(end=datetime.now(), periods=len(actual_data))
                    
                    logger.info(f"日期索引长度: {len(date_index)}")
                    
                    # 确保日期索引长度与数据长度匹配
                    if len(date_index) != len(actual_data):
                        logger.warning(f"日期索引长度({len(date_index)})与数据长度({len(actual_data)})不匹配，将重新生成日期索引")
                        date_index = pd.date_range(end=datetime.now(), periods=len(actual_data))
                        logger.info(f"重新生成的日期索引长度: {len(date_index)}")
                except Exception as e:
                    logger.error(f"生成日期索引时出错: {str(e)}")
                    logger.info("使用默认日期索引")
                    date_index = pd.date_range(end=datetime.now(), periods=len(actual_data))
                
                # 绘制实际股价
                try:
                    plt.plot(date_index, actual_data, label='实际股价', alpha=0.6)
                    logger.info("成功绘制实际股价")
                except Exception as e:
                    logger.error(f"绘制实际股价时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # 训练集预测
                try:
                    train_predict_plot = np.empty_like(actual_data)
                    train_predict_plot[:] = np.nan
                    
                    # 确保索引不超出范围
                    train_end_idx = min(args.time_step + len(train_predict), len(train_predict_plot))
                    logger.info(f"训练集预测起始索引: {args.time_step}, 结束索引: {train_end_idx}")
                    train_predict_plot[args.time_step:train_end_idx] = train_predict.flatten()[:train_end_idx-args.time_step]
                    
                    plt.plot(date_index, train_predict_plot, label='训练集预测', alpha=0.8)
                    logger.info("成功绘制训练集预测")
                except Exception as e:
                    logger.error(f"绘制训练集预测时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # 测试集预测
                try:
                    test_predict_plot = np.empty_like(actual_data)
                    test_predict_plot[:] = np.nan
                    
                    # 确保索引不超出范围
                    test_start_idx = len(train_predict) + args.time_step
                    test_end_idx = min(test_start_idx + len(test_predict), len(test_predict_plot))
                    logger.info(f"测试集预测起始索引: {test_start_idx}, 结束索引: {test_end_idx}")
                    
                    if test_end_idx > test_start_idx:
                        test_predict_plot[test_start_idx:test_end_idx] = test_predict.flatten()[:test_end_idx-test_start_idx]
                        plt.plot(date_index, test_predict_plot, label='测试集预测', alpha=0.8)
                        logger.info("成功绘制测试集预测")
                    else:
                        logger.warning("测试集预测索引范围无效，跳过绘制测试集预测")
                except Exception as e:
                    logger.error(f"绘制测试集预测时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # 未来预测
                try:
                    last_date = date_index[-1]
                    future_dates = [last_date + timedelta(days=i+1) for i in range(args.future_days)]
                    # 调整未来日期，跳过周末
                    for i in range(len(future_dates)):
                        while future_dates[i].weekday() >= 5:  # 5和6代表周六和周日
                            future_dates[i] += timedelta(days=1)
                    
                    future_values = [pred[0] for pred in future_predictions]
                    logger.info(f"未来预测日期数量: {len(future_dates)}, 未来预测值数量: {len(future_values)}")
                    
                    plt.plot(future_dates, future_values, 'r--', label='未来预测', alpha=0.8)
                    logger.info("成功绘制未来预测")
                except Exception as e:
                    logger.error(f"绘制未来预测时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # 设置图表属性
                try:
                    # 设置x轴日期格式
                    plt.gca().xaxis.set_major_formatter(mpl.dates.DateFormatter('%Y-%m-%d'))
                    plt.gca().xaxis.set_major_locator(mpl.dates.MonthLocator(interval=2))
                    plt.gcf().autofmt_xdate()  # 自动旋转日期标签
                    
                    plt.legend()
                    plt.xlabel('交易日')
                    plt.ylabel('股价')
                    plt.title(f'{stock_code}({stock_name}) - {args.model_type.upper()} 股票价格预测')
                    plt.grid(True, alpha=0.3)
                    logger.info("成功设置图表属性")
                except Exception as e:
                    logger.error(f"设置图表属性时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # 保存图表
                try:
                    plot_dir = 'plots'
                    os.makedirs(plot_dir, exist_ok=True)
                    plot_file = os.path.join(plot_dir, f"{stock_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    plt.savefig(plot_file)
                    logger.info(f"预测图表已保存到: {plot_file}")
                except Exception as e:
                    logger.error(f"保存图表时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # 显示图表
                try:
                    plt.show()
                    logger.info("成功显示图表")
                except Exception as e:
                    logger.error(f"显示图表时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            except Exception as e:
                logger.error(f"生成预测图表时出错: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
            
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def prepare_feature_data(df):
    """准备特征数据"""
    try:
        # 基础特征
        feature_columns = ['close']
        
        # 移动平均线特征
        ma_columns = [col for col in df.columns if col.startswith('MA') and col != 'MACD']
        if ma_columns:
            feature_columns.extend(ma_columns[:3])  # 只使用前3个MA
        
        # MACD特征
        macd_columns = ['MACD', 'MACD_Signal', 'MACD_Hist']
        for col in macd_columns:
            if col in df.columns:
                feature_columns.append(col)
        
        # RSI特征
        rsi_columns = [col for col in df.columns if col.startswith('RSI')]
        if rsi_columns:
            feature_columns.append(rsi_columns[0])  # 只使用第一个RSI
        
        # 布林带特征
        bb_columns = ['BB_Upper', 'BB_Middle', 'BB_Lower']
        for col in bb_columns:
            if col in df.columns:
                feature_columns.append(col)
        
        # 波动率特征
        if 'Volatility' in df.columns:
            feature_columns.append('Volatility')
        elif 'ATR' in df.columns:
            feature_columns.append('ATR')
        
        # 确保所有特征都存在
        feature_columns = [col for col in feature_columns if col in df.columns]
        
        # 如果特征太少，至少保留close和其他可用的基本特征
        if len(feature_columns) < 3:
            basic_features = ['close', 'open', 'high', 'low', 'volume']
            feature_columns = [col for col in basic_features if col in df.columns]
        
        # 删除包含NaN的行
        df_features = df[feature_columns].dropna()
        
        return df_features
    
    except Exception as e:
        print(f"准备特征数据时出错: {str(e)}")
        return df[['close']].dropna()  # 出错时只返回收盘价

def predict_future_prices(model, df_features, days=7, feature_dims=None):
    """预测未来价格"""
    try:
        # 获取最新的特征数据
        latest_data = df_features.values[-model.time_step:].copy()
        
        # 获取最近的收盘价，用于验证预测结果的合理性
        recent_close = df_features['close'].values[-30:]  # 最近30天的收盘价
        avg_price = np.mean(recent_close)
        std_price = np.std(recent_close)
        
        # 设置合理的价格波动范围（基于历史波动率）
        max_daily_change_ratio = max(0.1, 3 * np.std(np.diff(recent_close) / recent_close[:-1]))  # 最大日涨跌幅
        
        # 预测结果
        future_predictions = []
        
        # 逐日预测
        for _ in range(days):
            # 准备输入数据
            X = np.array([latest_data])
            
            # 预测下一天
            prediction = model.predict(X)
            
            # 验证预测结果的合理性
            last_close = latest_data[-1, 0]
            predicted_close = prediction[0][0]
            
            # 计算预测的涨跌幅
            change_ratio = abs(predicted_close - last_close) / last_close
            
            # 如果预测的涨跌幅超过合理范围，进行调整
            if change_ratio > max_daily_change_ratio:
                # 限制在合理的涨跌幅范围内
                direction = 1 if predicted_close > last_close else -1
                predicted_close = last_close * (1 + direction * max_daily_change_ratio)
                prediction[0][0] = predicted_close
            
            # 如果预测值偏离历史均值过远，进行适当拉回
            if abs(predicted_close - avg_price) > 3 * std_price:
                # 向均值方向拉回一定比例
                pull_back_ratio = 0.3
                predicted_close = predicted_close * (1 - pull_back_ratio) + avg_price * pull_back_ratio
                prediction[0][0] = predicted_close
            
            future_predictions.append(prediction[0])
            
            # 更新最新数据
            new_row = latest_data[-1].copy()
            new_row[0] = prediction[0][0]  # 更新收盘价
            
            # 移除最早的一行，添加新预测的一行
            latest_data = np.vstack([latest_data[1:], new_row])
        
        return future_predictions
    
    except Exception as e:
        print(f"预测未来价格时出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []

def main():
    parser = argparse.ArgumentParser(description='A股LSTM股价预测分析工具')
    parser.add_argument('stock', type=str, help='股票代码或名称（如：000001或平安银行）')
    parser.add_argument('--start_date', type=str, help='开始日期（格式：YYYYMMDD）', default=None)
    parser.add_argument('--end_date', type=str, help='结束日期（格式：YYYYMMDD）', default=None)
    parser.add_argument('--time_step', type=int, help='时间步长（默认：60）', default=60)
    parser.add_argument('--epochs', type=int, help='训练轮数（默认：20）', default=20)
    parser.add_argument('--batch_size', type=int, help='批次大小（默认：32）', default=32)
    parser.add_argument('--future_days', type=int, help='预测未来天数（默认：7）', default=7)
    parser.add_argument('--no_plot', action='store_true', help='不显示预测结果图表')
    parser.add_argument('--model_type', type=str, choices=['lstm', 'lstm_with_thoughts'], 
                        default='lstm_with_thoughts', help='模型类型：lstm或lstm_with_thoughts')
    parser.add_argument('--thought_dim', type=int, default=32, help='思维维度（默认：32）')
    parser.add_argument('--num_thoughts', type=int, default=5, help='思维数量（默认：5）')
    parser.add_argument('--num_heads', type=int, default=4, help='多头注意力头数（默认：4）')
    
    args = parser.parse_args()
    
    # 初始化日志管理器
    logger_manager = LoggerManager()
    logger = logger_manager.get_logger("lstm_predict")
    
    try:
        # 初始化技术分析器
        analyzer = TechnicalAnalyzer()
        
        # 获取纯净的股票代码
        stock_code = analyzer._get_pure_stock_code(args.stock)
        if not stock_code:
            logger.error(f"无法获取有效的股票代码: {args.stock}")
            sys.exit(1)
        
        logger.info(f"获取到纯净的股票代码: {stock_code}")
        
        # 如果未指定日期，默认获取近两年数据
        if args.start_date is None:
            start_date = (datetime.now() - timedelta(days=730)).strftime('%Y%m%d')
        else:
            start_date = args.start_date
            
        if args.end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        else:
            end_date = args.end_date
        
        logger.info(f"获取日期范围: {start_date} 到 {end_date}")
        
        # 直接使用akshare获取股票数据
        try:
            import akshare as ak
            
            # 获取股票名称
            stock_list = ak.stock_info_a_code_name()
            matched = stock_list[stock_list['code'] == stock_code]
            if not matched.empty:
                stock_name = matched.iloc[0]['name']
            else:
                stock_name = stock_code
                
            logger.info(f"获取到股票名称: {stock_name}")
            
            # 获取股票数据
            logger.info(f"使用akshare获取股票数据: {stock_code}")
            try:
                # 尝试使用stock_zh_a_hist函数
                logger.info("尝试使用stock_zh_a_hist函数获取数据...")
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
                logger.warning(f"使用stock_zh_a_hist获取数据失败: {str(e1)}")
                try:
                    # 尝试使用stock_zh_a_daily函数
                    logger.info("尝试使用stock_zh_a_daily函数获取数据...")
                    # 判断股票市场
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
                    logger.warning(f"使用stock_zh_a_daily获取数据失败: {str(e2)}")
                    try:
                        # 尝试使用stock_zh_a_hist_min_em函数
                        logger.info("尝试使用stock_zh_a_hist_min_em函数获取数据...")
                        df = ak.stock_zh_a_hist_min_em(
                            symbol=stock_code,
                            start_date=start_date.replace('-', ''),
                            end_date=end_date.replace('-', ''),
                            period='daily',
                            adjust='qfq'
                        )
                        if df is None or df.empty:
                            raise Exception("获取数据为空")
                    except Exception as e3:
                        logger.error(f"所有尝试都失败: {str(e1)}, {str(e2)}, {str(e3)}")
                        
                        # 最后尝试使用baostock获取数据
                        logger.info("尝试使用baostock获取数据...")
                        try:
                            import baostock as bs
                            # 不要在这里重新导入pandas，使用全局导入的pd
                            
                            # 登录系统
                            lg = bs.login()
                            if lg.error_code != '0':
                                logger.error(f"baostock登录失败: {lg.error_msg}")
                                raise Exception("baostock登录失败")
                                
                            # 获取股票数据
                            rs = bs.query_history_k_data_plus(
                                code=f"{'sh' if stock_code.startswith(('6', '9')) else 'sz'}.{stock_code}",
                                fields="date,open,high,low,close,volume,amount",
                                start_date=start_date.replace('-', ''),
                                end_date=end_date.replace('-', ''),
                                frequency="d",
                                adjustflag="2"  # 前复权
                            )
                            if rs.error_code != '0':
                                logger.error(f"baostock获取数据失败: {rs.error_msg}")
                                raise Exception("baostock获取数据失败")
                                
                            # 处理数据
                            data_list = []
                            while (rs.next()):
                                data_list.append(rs.get_row_data())
                            
                            # 登出系统
                            bs.logout()
                            
                            # 转换为DataFrame
                            df = pd.DataFrame(data_list, columns=rs.fields)
                            
                            # 转换数据类型
                            for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
                                if col in df.columns:
                                    df[col] = pd.to_numeric(df[col])
                                    
                            # 设置日期列
                            df['date'] = pd.to_datetime(df['date'])
                            
                            if df is None or df.empty:
                                raise Exception("baostock获取数据为空")
                                
                            logger.info("成功使用baostock获取数据")
                            
                        except Exception as e4:
                            logger.error(f"使用baostock获取数据失败: {str(e4)}")
                            raise Exception(f"无法获取股票数据: {stock_code}")
            
            if df is None or df.empty:
                logger.error(f"akshare返回的数据为空: {stock_code}")
                sys.exit(1)
                
            logger.info(f"成功获取到股票数据，共 {len(df)} 条记录")
            
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
            
        except Exception as e:
            logger.error(f"使用akshare获取数据失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # 不要直接退出，而是尝试使用get_stock_data_with_indicators函数获取数据
            logger.info("尝试使用get_stock_data_with_indicators函数获取数据...")
            df_with_indicators, stock_name = get_stock_data_with_indicators(stock_code, start_date, end_date, logger)
            if df_with_indicators is None:
                logger.error("无法获取股票数据，程序退出")
                sys.exit(1)
            logger.info(f"成功获取到股票数据，共 {len(df_with_indicators)} 条记录")
            
            # 使用获取到的数据继续处理
            df = df_with_indicators
        
        # 准备特征数据
        df_features = prepare_feature_data(df)
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
        logger.info("开始训练模型...")
        model.train(X_train, Y_train, epochs=args.epochs, batch_size=args.batch_size)
        
        # 进行预测
        logger.info("生成预测结果...")
        train_predict = model.predict(X_train)
        test_predict = model.predict(X_test)
        
        # 预测未来价格
        logger.info(f"预测未来 {args.future_days} 天的价格...")
        future_predictions = predict_future_prices(model, df_features, days=args.future_days, feature_dims=feature_dims)
        
        # 评估模型
        metrics = model.evaluate(X_test, Y_test)
        logger.info("模型评估指标：")
        logger.info(f"均方误差 (MSE): {metrics['MSE']:.4f}")
        logger.info(f"均方根误差 (RMSE): {metrics['RMSE']:.4f}")
        logger.info(f"平均绝对误差 (MAE): {metrics['MAE']:.4f}")
        logger.info(f"平均绝对百分比误差 (MAPE): {metrics['MAPE']:.4f}%")
        
        # 输出未来预测结果
        logger.info("\n未来价格预测结果：")
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
        save_results(stock_code, stock_name, metrics, future_predictions)
        
        # 显示预测图表
        if not args.no_plot:
            try:
                logger.info("开始生成预测图表...")
                # 绘制历史数据和预测结果
                plt.figure(figsize=(14, 8))
                
                # 设置中文字体
                try:
                    import matplotlib as mpl
                    # 尝试设置中文字体
                    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
                    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                    logger.info("成功设置中文字体")
                except Exception as e:
                    logger.warning(f"设置中文字体失败: {str(e)}")
                    # 使用英文标题
                    stock_name = f"{stock_code}"
                
                # 实际收盘价
                actual_data = df_features['close'].values
                logger.info(f"实际数据长度: {len(actual_data)}")
                
                # 获取日期索引
                try:
                    if hasattr(df, 'index') and len(df.index) > 0:
                        logger.info(f"使用DataFrame索引作为日期索引，索引长度: {len(df.index)}")
                        # 确保日期索引长度与数据长度匹配
                        if len(df.index) >= len(actual_data):
                            date_index = df.index[-len(actual_data):]
                            logger.info(f"使用DataFrame索引的后 {len(actual_data)} 个元素")
                        else:
                            logger.warning(f"DataFrame索引长度({len(df.index)})小于数据长度({len(actual_data)})，将生成新的日期索引")
                            date_index = pd.date_range(end=datetime.now(), periods=len(actual_data))
                    else:
                        logger.warning("DataFrame没有索引或索引为空，将生成新的日期索引")
                        date_index = pd.date_range(end=datetime.now(), periods=len(actual_data))
                    
                    logger.info(f"日期索引长度: {len(date_index)}")
                    
                    # 确保日期索引长度与数据长度匹配
                    if len(date_index) != len(actual_data):
                        logger.warning(f"日期索引长度({len(date_index)})与数据长度({len(actual_data)})不匹配，将重新生成日期索引")
                        date_index = pd.date_range(end=datetime.now(), periods=len(actual_data))
                        logger.info(f"重新生成的日期索引长度: {len(date_index)}")
                except Exception as e:
                    logger.error(f"生成日期索引时出错: {str(e)}")
                    logger.info("使用默认日期索引")
                    date_index = pd.date_range(end=datetime.now(), periods=len(actual_data))
                
                # 绘制实际股价
                try:
                    plt.plot(date_index, actual_data, label='实际股价', alpha=0.6)
                    logger.info("成功绘制实际股价")
                except Exception as e:
                    logger.error(f"绘制实际股价时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # 训练集预测
                try:
                    train_predict_plot = np.empty_like(actual_data)
                    train_predict_plot[:] = np.nan
                    
                    # 确保索引不超出范围
                    train_end_idx = min(args.time_step + len(train_predict), len(train_predict_plot))
                    logger.info(f"训练集预测起始索引: {args.time_step}, 结束索引: {train_end_idx}")
                    train_predict_plot[args.time_step:train_end_idx] = train_predict.flatten()[:train_end_idx-args.time_step]
                    
                    plt.plot(date_index, train_predict_plot, label='训练集预测', alpha=0.8)
                    logger.info("成功绘制训练集预测")
                except Exception as e:
                    logger.error(f"绘制训练集预测时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # 测试集预测
                try:
                    test_predict_plot = np.empty_like(actual_data)
                    test_predict_plot[:] = np.nan
                    
                    # 确保索引不超出范围
                    test_start_idx = len(train_predict) + args.time_step
                    test_end_idx = min(test_start_idx + len(test_predict), len(test_predict_plot))
                    logger.info(f"测试集预测起始索引: {test_start_idx}, 结束索引: {test_end_idx}")
                    
                    if test_end_idx > test_start_idx:
                        test_predict_plot[test_start_idx:test_end_idx] = test_predict.flatten()[:test_end_idx-test_start_idx]
                        plt.plot(date_index, test_predict_plot, label='测试集预测', alpha=0.8)
                        logger.info("成功绘制测试集预测")
                    else:
                        logger.warning("测试集预测索引范围无效，跳过绘制测试集预测")
                except Exception as e:
                    logger.error(f"绘制测试集预测时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # 未来预测
                try:
                    last_date = date_index[-1]
                    future_dates = [last_date + timedelta(days=i+1) for i in range(args.future_days)]
                    # 调整未来日期，跳过周末
                    for i in range(len(future_dates)):
                        while future_dates[i].weekday() >= 5:  # 5和6代表周六和周日
                            future_dates[i] += timedelta(days=1)
                    
                    future_values = [pred[0] for pred in future_predictions]
                    logger.info(f"未来预测日期数量: {len(future_dates)}, 未来预测值数量: {len(future_values)}")
                    
                    plt.plot(future_dates, future_values, 'r--', label='未来预测', alpha=0.8)
                    logger.info("成功绘制未来预测")
                except Exception as e:
                    logger.error(f"绘制未来预测时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # 设置图表属性
                try:
                    # 设置x轴日期格式
                    plt.gca().xaxis.set_major_formatter(mpl.dates.DateFormatter('%Y-%m-%d'))
                    plt.gca().xaxis.set_major_locator(mpl.dates.MonthLocator(interval=2))
                    plt.gcf().autofmt_xdate()  # 自动旋转日期标签
                    
                    plt.legend()
                    plt.xlabel('交易日')
                    plt.ylabel('股价')
                    plt.title(f'{stock_code}({stock_name}) - {args.model_type.upper()} 股票价格预测')
                    plt.grid(True, alpha=0.3)
                    logger.info("成功设置图表属性")
                except Exception as e:
                    logger.error(f"设置图表属性时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # 保存图表
                try:
                    plot_dir = 'plots'
                    os.makedirs(plot_dir, exist_ok=True)
                    plot_file = os.path.join(plot_dir, f"{stock_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    plt.savefig(plot_file)
                    logger.info(f"预测图表已保存到: {plot_file}")
                except Exception as e:
                    logger.error(f"保存图表时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # 显示图表
                try:
                    plt.show()
                    logger.info("成功显示图表")
                except Exception as e:
                    logger.error(f"显示图表时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            except Exception as e:
                logger.error(f"生成预测图表时出错: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
            
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main() 