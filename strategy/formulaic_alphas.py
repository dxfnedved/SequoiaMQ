# -*- encoding: UTF-8 -*-
import numpy as np
import pandas as pd
import talib as tl
import logging

# 创建专门的logger
logger = logging.getLogger('Alpha_Strategy')

# 参数设置
PRICE_LIMIT = 0.1  # 涨跌停限制 10%
VOL_THRESHOLD = 2.0  # 成交量放大倍数阈值
MA_PERIODS = [5, 10, 20]  # 均线周期

def handle_limit_up_down(data):
    """处理涨跌停限制"""
    data['涨跌幅'] = data['收盘'].pct_change()
    data['涨跌幅'] = data['涨跌幅'].clip(-PRICE_LIMIT, PRICE_LIMIT)
    return data

def handle_suspension(data):
    """处理停牌"""
    return data[data['成交量'] > 0].copy()

def calculate_alpha1(data):
    """动量因子：结合波动率的趋势跟踪"""
    returns = data['涨跌幅']
    close = data['收盘']
    
    stddev = returns.rolling(window=20).std()
    condition = returns < 0
    result = np.where(condition, stddev, close)
    signed_power = np.sign(result) * (np.abs(result) ** 2)
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
            return False
        
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
            logger.info(f"Alpha策略 - {code} - 买入信号 "
                       f"[动量:{current['alpha1']:.2f}, "
                       f"量价:{current['volume_factor']:.2f}, "
                       f"反转:{current['reversal_factor']:.2f}]")
            return True
            
    except Exception as e:
        logger.error(f"处理股票{code}时出错：{str(e)}")
        return False
    
    return False

def check_sell_signals(code, data, end_date=None):
    """卖出信号判断"""
    try:
        # 数据预处理
        data = handle_limit_up_down(data)
        data = handle_suspension(data)
        
        if len(data) < 30:
            return False
        
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
        
        if any(conditions):  # 满足任一条件即卖出
            logger.info(f"Alpha策略 - {code} - 卖出信号 "
                       f"[动量:{current['alpha1']:.2f}, "
                       f"量价:{current['volume_factor']:.2f}, "
                       f"反转:{current['reversal_factor']:.2f}]")
            return True
            
    except Exception as e:
        logger.error(f"处理股票{code}时出错：{str(e)}")
        return False
    
    return False

def check(code, data, end_date=None):
    """主要的策略判断函数"""
    buy_signal = check_buy_signals(code, data, end_date)
    sell_signal = check_sell_signals(code, data, end_date)
    
    return buy_signal
