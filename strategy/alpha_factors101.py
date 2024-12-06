# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
import talib as ta

def calculate_alpha1(data):
    """
    Alpha#1: (rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)
    """
    returns = data['收盘'].pct_change()
    stddev = returns.rolling(window=20).std()
    close = data['收盘']
    
    # 计算SignedPower部分
    condition = returns < 0
    base = np.where(condition, stddev, close)
    signed_power = np.sign(base) * (np.abs(base) ** 2)
    
    # 计算最近5天内最大值的位置
    rolling_max = pd.Series(signed_power).rolling(window=5).apply(lambda x: x.argmax())
    
    # 归一化到[-1, 1]区间
    alpha = (rolling_max / 4) - 0.5
    return alpha

def calculate_alpha2(data):
    """
    Alpha#2: (-1 * correlation(rank(delta(log(volume), 2)), rank((close - open) / open), 6))
    """
    volume = data['成交量']
    close = data['收盘']
    open_price = data['开盘']
    
    # 计算log(volume)的2日差分
    delta_log_volume = np.log(volume).diff(2)
    
    # 计算(close - open) / open
    returns_intraday = (close - open_price) / open_price
    
    # 计算6日相关系数
    corr = delta_log_volume.rolling(window=6).corr(returns_intraday)
    
    return -1 * corr

def calculate_alpha3(data):
    """
    Alpha#3: (-1 * correlation(rank(open), rank(volume), 10))
    """
    open_price = data['开盘']
    volume = data['成交量']
    
    # 计算10日相关系数
    corr = open_price.rolling(window=10).corr(volume)
    
    return -1 * corr

def calculate_alpha4(data):
    """
    Alpha#4: (-1 * Ts_Rank(rank(low), 9))
    """
    low = data['最低']
    
    # 计算9日排序
    ts_rank = low.rolling(window=9).apply(lambda x: pd.Series(x).rank().iloc[-1])
    
    return -1 * ts_rank

def check(stock_code, data, end_date=None):
    """
    多因子策略检查
    
    Args:
        stock_code: 股票代码
        data: 股票数据
        end_date: 结束日期
    
    Returns:
        bool: True表示买入信号，False表示不买入
    """
    if len(data) < 20:  # 数据不足时不产生信号
        return False
    
    try:
        # 计算各个Alpha因子
        alpha1 = calculate_alpha1(data)
        alpha2 = calculate_alpha2(data)
        alpha3 = calculate_alpha3(data)
        alpha4 = calculate_alpha4(data)
        
        # 获取最新的因子值
        latest_alpha1 = alpha1.iloc[-1]
        latest_alpha2 = alpha2.iloc[-1]
        latest_alpha3 = alpha3.iloc[-1]
        latest_alpha4 = alpha4.iloc[-1]
        
        # 设置阈值
        ALPHA1_THRESHOLD = 0.3
        ALPHA2_THRESHOLD = 0.2
        ALPHA3_THRESHOLD = -0.3
        ALPHA4_THRESHOLD = -0.25
        
        # 综合判断多个因子
        buy_signal = (
            latest_alpha1 > ALPHA1_THRESHOLD and
            latest_alpha2 > ALPHA2_THRESHOLD and
            latest_alpha3 < ALPHA3_THRESHOLD and
            latest_alpha4 < ALPHA4_THRESHOLD
        )
        
        return buy_signal
        
    except Exception as e:
        print(f"计算Alpha因子时出错: {str(e)}")
        return False 