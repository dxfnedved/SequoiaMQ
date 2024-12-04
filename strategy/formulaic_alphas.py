# -*- encoding: UTF-8 -*-
import numpy as np
import pandas as pd
import talib as tl
import logging

# 创建专门的logger
logger = logging.getLogger('Alpha_Strategy')

def calculate_alpha1(data):
    """Alpha#1: (rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)"""
    returns = data['p_change'] / 100
    close = data['收盘']
    
    # 计算20日收益率标准差
    stddev = returns.rolling(window=20).std()
    
    # 构建条件数组
    condition = returns < 0
    result = np.where(condition, stddev, close)
    
    # 计算SignedPower
    signed_power = np.sign(result) * (np.abs(result) ** 2)
    
    # 计算5日内最大值的位置
    ts_argmax = signed_power.rolling(window=5).apply(np.argmax)
    
    return ts_argmax

def calculate_alpha6(data):
    """Alpha#6: -1 * correlation(open, volume, 10)"""
    open_prices = data['开盘']
    volume = data['成交量']
    
    corr = open_prices.rolling(window=10).corr(volume)
    return -1 * corr

def calculate_alpha26(data):
    """Alpha#26: -1 * max(correlation(ts_rank(volume, 5), ts_rank(high, 5), 5), 3)"""
    high = data['最高']
    volume = data['成交量']
    
    # 计算5日排名
    ts_rank_volume = volume.rolling(window=5).apply(lambda x: pd.Series(x).rank().iloc[-1])
    ts_rank_high = high.rolling(window=5).apply(lambda x: pd.Series(x).rank().iloc[-1])
    
    # 计算相关系数
    corr = ts_rank_volume.rolling(window=5).corr(ts_rank_high)
    return -1 * corr.rolling(window=3).max()

def check_buy_signals(code, data, end_date=None):
    """
    买入信号判断
    """
    if len(data) < 30:
        return False
    
    try:
        # 计算Alpha因子
        data['alpha1'] = calculate_alpha1(data)
        data['alpha6'] = calculate_alpha6(data)
        data['alpha26'] = calculate_alpha26(data)
        
        # 获取最新数据
        current = data.iloc[-1]
        prev = data.iloc[-2]
        
        # 买入条件
        conditions = [
            current['alpha1'] > prev['alpha1'],  # Alpha1上升
            current['alpha6'] < -0.3,            # Alpha6为负相关
            current['alpha26'] < -0.2,           # Alpha26为负值
            current['成交量'] > data['成交量'].rolling(window=20).mean().iloc[-1],  # 成交量大于20日均量
            current['收盘'] > current['开盘'],    # 收盘价大于开盘价
        ]
        
        if all(conditions):
            return True
            
    except Exception as e:
        print(f"处理股票{code}时出错：{str(e)}")
        return False
    
    return False

def check_sell_signals(code, data, end_date=None):
    """
    卖出信号判断
    """
    if len(data) < 30:
        return False
    
    try:
        # 计算Alpha因子
        data['alpha1'] = calculate_alpha1(data)
        data['alpha6'] = calculate_alpha6(data)
        data['alpha26'] = calculate_alpha26(data)
        
        # 获取最新数据
        current = data.iloc[-1]
        prev = data.iloc[-2]
        
        # 卖出条件
        conditions = [
            current['alpha1'] < prev['alpha1'],  # Alpha1下降
            current['alpha6'] > 0.3,             # Alpha6为正相关
            current['alpha26'] > 0.2,            # Alpha26为正值
            current['成交量'] < data['成交量'].rolling(window=20).mean().iloc[-1],  # 成交量小于20日均量
            current['收盘'] < current['开盘'],     # 收盘价小于开盘价
        ]
        
        if any(conditions):  # 满足任一条件即卖出
            return True
            
    except Exception as e:
        print(f"处理股票{code}时出错：{str(e)}")
        return False
    
    return False

def check(code, data, end_date=None):
    """主要的策略判断函数"""
    if len(data) < 30:
        return False
    
    try:
        # 计算Alpha因子
        data['alpha1'] = calculate_alpha1(data)
        data['alpha6'] = calculate_alpha6(data)
        data['alpha26'] = calculate_alpha26(data)
        
        # 获取最新数据
        current = data.iloc[-1]
        prev = data.iloc[-2]
        
        # 检查买入和卖出信号
        buy_signal = check_buy_signals(code, data, end_date)
        sell_signal = check_sell_signals(code, data, end_date)
        
        # 简洁的日志输出
        signal_type = "买入" if buy_signal else "卖出" if sell_signal else "观望"
        logger.info(f"Alpha策略 - {code} - {signal_type} "
                   f"[A1:{current['alpha1']:.2f}, "
                   f"A6:{current['alpha6']:.2f}, "
                   f"A26:{current['alpha26']:.2f}]")
        
        return buy_signal
            
    except Exception as e:
        logger.error(f"处理股票{code}时出错：{str(e)}")
        return False
