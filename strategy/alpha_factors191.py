# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
import talib as ta

def calculate_alpha1(data):
    """
    Alpha#1: (-1 * CORR(RANK(DELTA(LOG(VOLUME), 1)), RANK(((CLOSE - OPEN) / OPEN)), 6))
    相关性因子，衡量成交量变化和日内收益率的排序相关性
    """
    volume = data['成交量']
    close = data['收盘']
    open_price = data['开盘']
    
    # 计算DELTA(LOG(VOLUME), 1)
    delta_log_volume = np.log(volume).diff(1)
    
    # 计算((CLOSE - OPEN) / OPEN)
    intraday_return = (close - open_price) / open_price
    
    # 计算排序相关性
    rank_delta_log_volume = delta_log_volume.rank(pct=True)
    rank_intraday_return = intraday_return.rank(pct=True)
    
    # 计算6日相关系数
    correlation = rank_delta_log_volume.rolling(window=6).corr(rank_intraday_return)
    
    return -1 * correlation

def calculate_alpha2(data):
    """
    Alpha#2: (-1 * DELTA((((CLOSE - LOW) - (HIGH - CLOSE)) / (HIGH - LOW)), 1))
    价格位置因子，衡量收盘价在当日价格区间中的位置变化
    """
    close = data['收盘']
    high = data['最高']
    low = data['最低']
    
    # 计算价格位置
    price_position = ((close - low) - (high - close)) / (high - low)
    
    # 计算1日差分
    delta = price_position.diff(1)
    
    return -1 * delta

def calculate_alpha3(data):
    """
    Alpha#3: SUM((CLOSE=DELAY(CLOSE,1)?0:CLOSE-(CLOSE>DELAY(CLOSE,1)?MIN(LOW,DELAY(CLOSE,1)):MAX(HIGH,DELAY(CLOSE,1)))),6)
    趋势突破因子，衡量价格突破前期高低点的强度
    """
    close = data['收盘']
    high = data['最高']
    low = data['最低']
    delay_close = close.shift(1)
    
    # 计算条件表达式
    condition1 = close == delay_close
    condition2 = close > delay_close
    
    # 计算价格突破
    max_price = np.maximum(high, delay_close)
    min_price = np.minimum(low, delay_close)
    
    # 计算突破强度
    breakthrough = np.where(condition1, 0,
                          np.where(condition2, 
                                 close - min_price,
                                 close - max_price))
    
    # 计算6日累和
    return pd.Series(breakthrough).rolling(window=6).sum()

def calculate_alpha4(data):
    """
    Alpha#4: ((((SUM(CLOSE, 8) / 8) + STD(CLOSE, 8)) < (SUM(CLOSE, 2) / 2)) ? (-1 * 1) : 
             (((SUM(CLOSE, 2) / 2) < ((SUM(CLOSE, 8) / 8) - STD(CLOSE, 8))) ? 1 : 
             (((1 < (VOLUME / MEAN(VOLUME,20))) || ((VOLUME / MEAN(VOLUME,20)) == 1)) ? 1 : (-1 * 1))))
    均线和波动率组合因子
    """
    close = data['收盘']
    volume = data['成交量']
    
    # 计算移动平均和标准差
    ma8 = close.rolling(window=8).mean()
    std8 = close.rolling(window=8).std()
    ma2 = close.rolling(window=2).mean()
    volume_ma20 = volume.rolling(window=20).mean()
    
    # 计算条件
    condition1 = (ma8 + std8) < ma2
    condition2 = ma2 < (ma8 - std8)
    condition3 = volume > volume_ma20
    
    # 组合信号
    alpha = np.where(condition1, -1,
                    np.where(condition2, 1,
                            np.where(condition3, 1, -1)))
    
    return pd.Series(alpha)

def normalize_factor(factor):
    """
    因子标准化
    """
    return (factor - factor.rolling(window=20).mean()) / factor.rolling(window=20).std()

def check(stock_code, data, end_date=None):
    """
    Alpha191多因子策略检查
    
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
        factors = {
            'alpha1': calculate_alpha1(data),
            'alpha2': calculate_alpha2(data),
            'alpha3': calculate_alpha3(data),
            'alpha4': calculate_alpha4(data)
        }
        
        # 标准化因子
        normalized_factors = {name: normalize_factor(factor) 
                            for name, factor in factors.items()}
        
        # 获取最新的因子值
        latest_factors = {name: factor.iloc[-1] 
                         for name, factor in normalized_factors.items()}
        
        # 因子权重
        weights = {
            'alpha1': 0.25,
            'alpha2': 0.25,
            'alpha3': 0.25,
            'alpha4': 0.25
        }
        
        # 计算综合得分
        composite_score = sum(latest_factors[factor] * weight 
                            for factor, weight in weights.items())
        
        # 设置买入阈值
        SCORE_THRESHOLD = 0.5
        
        # 生成买入信号
        return composite_score > SCORE_THRESHOLD
        
    except Exception as e:
        print(f"计算Alpha191因子时出错: {str(e)}")
        return False

def get_factor_exposure(data):
    """
    获取因子暴露度
    用于分析和监控因子表现
    """
    try:
        exposures = {
            'alpha1': calculate_alpha1(data),
            'alpha2': calculate_alpha2(data),
            'alpha3': calculate_alpha3(data),
            'alpha4': calculate_alpha4(data)
        }
        
        # 标准化因子暴露度
        normalized_exposures = {name: normalize_factor(exposure) 
                              for name, exposure in exposures.items()}
        
        return normalized_exposures
        
    except Exception as e:
        print(f"计算因子暴露度时出错: {str(e)}")
        return None 