# -*- encoding: UTF-8 -*-
import os
import pandas as pd
from datetime import datetime
import talib as tl
import logging
import numpy as np
from collections import defaultdict
import time
import data_fetcher
import push

# 创建专门的logger
logger = logging.getLogger('Alpha_Strategy')

# 参数设置
PRICE_LIMIT = 0.1  # 涨跌停限制 10%
VOL_THRESHOLD = 2.0  # 成交量放大倍数阈值
MA_PERIODS = [5, 10, 20]  # 均线周期

# 添加结果保存目录
RESULTS_DIR = "results"

def ensure_dir_exists(directory):
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def save_strategy_results(stock_signals, date_str):
    """保存策略结果到CSV文件"""
    ensure_dir_exists(RESULTS_DIR)
    
    # 创建结果DataFrame
    results = []
    for code, signals in stock_signals.items():
        stock_code, stock_name = code
        for strategy, signal in signals:
            if signal == "买入":
                results.append({
                    '日期': date_str,
                    '股票代码': stock_code,
                    '股票名称': stock_name,
                    '策略': strategy,
                    '信号': signal
                })
    
    if results:
        df = pd.DataFrame(results)
        file_path = os.path.join(RESULTS_DIR, f'strategy_signals_{date_str}.csv')
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        logging.info(f"策略信号已保存到: {file_path}")

def save_statistics_results(stats_data, date_str):
    """保存市场统计数据到CSV"""
    ensure_dir_exists(RESULTS_DIR)
    
    file_path = os.path.join(RESULTS_DIR, f'market_stats_{date_str}.csv')
    pd.DataFrame([stats_data]).to_csv(file_path, index=False, encoding='utf-8-sig')
    logging.info(f"市场统计数据已保存到: {file_path}")

def process(stocks, strategies):
    date_str = datetime.now().strftime('%Y%m%d')
    stocks_data = data_fetcher.run(stocks)
    stock_signals = defaultdict(list)
    strategy_stats = defaultdict(int)
    
    for strategy, strategy_func in strategies.items():
        results = check_strategy(stocks_data, strategy, strategy_func)
        for code, signal in results.items():
            stock_signals[code].append((strategy, signal))
            if signal == "买入":
                strategy_stats[strategy] += 1
        time.sleep(2)
    
    # 保存策略信号
    save_strategy_results(stock_signals, date_str)
    
    # 输出简要统计信息到日志
    logging.info("--- 策略统计 ---")
    for strategy, count in strategy_stats.items():
        logging.info(f"{strategy}: {count}个买入信号")

def statistics(all_data, stocks):
    date_str = datetime.now().strftime('%Y%m%d')
    
    stats_data = {
        '日期': date_str,
        '涨停数量': len(all_data.loc[(all_data['涨跌幅'] >= 9.5)]),
        '跌停数量': len(all_data.loc[(all_data['涨跌幅'] <= -9.5)]),
        '涨幅大于5%数量': len(all_data.loc[(all_data['涨跌幅'] >= 5)]),
        '跌幅大于5%数量': len(all_data.loc[(all_data['涨跌幅'] <= -5)]),
        '总股票数量': len(stocks)
    }
    
    # 保存统计数据
    save_statistics_results(stats_data, date_str)
    
    # 发送消息通知
    msg = ("涨停数：{涨停数量}   跌停数：{跌停数量}\n"
           "涨幅大于5%数：{涨幅大于5%数量}  跌幅大于5%数量：{跌幅大于5%数量}").format(**stats_data)
    push.statistics(msg)

def handle_limit_up_down(data):
    """处理涨跌停限制"""
    data['涨跌幅'] = data['收盘'].pct_change()
    data['涨跌幅'] = data['涨跌幅'].clip(-PRICE_LIMIT, PRICE_LIMIT)
    return data

def handle_suspension(data):
    """处理停牌"""
    return data[data['成交量'] > 0].copy()

def calculate_alpha1(data):
    """Alpha#1: (rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)"""
    # 确保数据是pandas Series
    returns = pd.Series(data['p_change'] / 100)
    close = pd.Series(data['收盘'])
    
    # 计算20日收益率标准差
    stddev = returns.rolling(window=20).std()
    
    # 构建条件数组
    condition = returns < 0
    result = pd.Series(np.where(condition, stddev, close))
    
    # 计算SignedPower
    signed_power = pd.Series(np.sign(result) * (np.abs(result) ** 2))
    
    # 计算5日内最大值的位置
    ts_argmax = signed_power.rolling(window=5).apply(np.argmax)
    
    return ts_argmax

def calculate_volume_factor(data):
    """成交量因子：量价相关性"""
    volume = data['成交量']
    close = data['收盘']
    
    # 计算成交量变化
    vol_ma5 = volume.rolling(window=5).mean()
    vol_ratio = volume / vol_ma5
    
    # 计算价格动量
    price_momentum = close.pct_change(5)
    
    return vol_ratio * np.sign(price_momentum)

def calculate_reversal_factor(data):
    """反转因子：超跌反弹"""
    high = data['最高']
    low = data['最低']
    close = data['收盘']
    
    # 计算超跌程度
    hl_range = (high - low) / low
    close_position = (close - low) / (high - low)
    
    return -1 * close_position * hl_range

def check_buy_signals(code, data, end_date=None):
    """买入信号判断"""
    try:
        # 数据预处理
        data = handle_limit_up_down(data)
        data = handle_suspension(data)
        
        if len(data) < 30:
            return False, {}
        
        # 计算因子
        data['alpha1'] = calculate_alpha1(data)
        data['volume_factor'] = calculate_volume_factor(data)
        data['reversal_factor'] = calculate_reversal_factor(data)
        
        # 获取最新数据
        current = data.iloc[-1]
        prev = data.iloc[-2]
        
        # 买入条件
        conditions = [
            current['alpha1'] > prev['alpha1'],  # 动量上升
            current['volume_factor'] > VOL_THRESHOLD,  # 成交量放大
            current['reversal_factor'] < -0.2,  # 超跌反弹机会
            current['成交量'] > data['成交量'].rolling(window=20).mean().iloc[-1],  # 放量
            all(current['收盘'] > data[f'MA{period}'].iloc[-1] for period in MA_PERIODS)  # 均线多头
        ]
        
        if all(conditions):
            signal_info = {
                '动量': current['alpha1'],
                '量价': current['volume_factor'],
                '反转': current['reversal_factor']
            }
            return True, signal_info
            
    except Exception as e:
        logger.error(f"处理股票{code}时出错：{str(e)}")
        return False, {}
    
    return False, {}

def check_sell_signals(code, data, end_date=None):
    """卖出信号判断"""
    try:
        # 数据预处理
        data = handle_limit_up_down(data)
        data = handle_suspension(data)
        
        if len(data) < 30:
            return False, {}
        
        # 计算因子
        data['alpha1'] = calculate_alpha1(data)
        data['volume_factor'] = calculate_volume_factor(data)
        data['reversal_factor'] = calculate_reversal_factor(data)
        
        # 获取最新数据
        current = data.iloc[-1]
        prev = data.iloc[-2]
        
        # 卖出条件
        conditions = [
            current['alpha1'] < prev['alpha1'],  # 动量下降
            current['volume_factor'] < 0.5,  # 量能萎缩
            current['reversal_factor'] > 0.2,  # 上涨乏力
            current['成交量'] < data['成交量'].rolling(window=20).mean().iloc[-1],  # 缩量
            any(current['收盘'] < data[f'MA{period}'].iloc[-1] for period in MA_PERIODS)  # 跌破均线
        ]
        
        if any(conditions):
            signal_info = {
                '动量': current['alpha1'],
                '量价': current['volume_factor'],
                '反转': current['reversal_factor']
            }
            return True, signal_info
            
    except Exception as e:
        logger.error(f"处理股票{code}时出错：{str(e)}")
        return False, {}
    
    return False, {}

def check(code, data, end_date=None):
    """主要的策略判断函数"""
    buy_signal, buy_info = check_buy_signals(code, data, end_date)
    sell_signal, sell_info = check_sell_signals(code, data, end_date)
    
    # 记录详细信号信息到CSV
    if buy_signal or sell_signal:
        signal_info = buy_info if buy_signal else sell_info
        save_signal_details(code, "买入" if buy_signal else "卖出", signal_info)
    
    return buy_signal

def save_signal_details(code, signal_type, signal_info):
    """保存详细的信号信息"""
    date_str = datetime.now().strftime('%Y%m%d')
    file_path = os.path.join('results', 'alpha_signals_details.csv')
    
    data = {
        '日期': date_str,
        '股票代码': code,
        '信号类型': signal_type,
        **signal_info
    }
    
    # 追加模式写入CSV
    df = pd.DataFrame([data])
    if os.path.exists(file_path):
        df.to_csv(file_path, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        df.to_csv(file_path, index=False, encoding='utf-8-sig')

def check_strategy(stocks_data, strategy_name, strategy_func):
    """检查策略的买入卖出信号"""
    results = {}
    for code, data in stocks_data.items():
        try:
            if strategy_func(code, data):
                results[code] = "买入"
        except Exception as e:
            logger.error(f"策略{strategy_name}处理股票{code}时出错：{str(e)}")
    return results
