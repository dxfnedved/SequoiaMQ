# -*- coding: UTF-8 -*-
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import logging

# 创建策略专用的logger
logger = logging.getLogger('RARA_Strategy')

# 参数设置
OBSERVATION_PERIOD = 250  # 观察周期M改为一年的交易日数量
BUY_THRESHOLD = 0.7      # 买入阈值
SELL_THRESHOLD = -0.7    # 卖出阈值
MIN_PERIODS = 20        # 最小计算周期

def calculate_beta(data):
    """计算单个beta值"""
    if data is None or len(data) < 2:
        return None
    
    try:
        if '最高' not in data.columns or '最低' not in data.columns:
            logger.error(f"数据缺少必要的列: {data.columns}")
            return None
            
        X = data['最高'].values.reshape(-1, 1)
        y = data['最低'].values
        
        reg = LinearRegression()
        reg.fit(X, y)
        return reg.coef_[0]
    except Exception as e:
        logger.error(f"计算beta值错误: {str(e)}")
        return None

def calculate_rsrs_std_score(data, period=OBSERVATION_PERIOD, min_periods=MIN_PERIODS):
    """计算RSRS标准分"""
    if data is None or len(data) < min_periods:
        return None
    
    try:
        # 计算每个窗口的beta值
        betas = []
        for i in range(len(data) - min_periods + 1):
            window_data = data.iloc[i:i+min_periods]
            beta = calculate_beta(window_data)
            betas.append(beta)
        
        # 将前min_periods-1个位置的beta设为None
        betas = [None] * (min_periods-1) + betas
        
        # 转换为Series以便计算移动平均和标准差
        beta_series = pd.Series(betas)
        beta_mean = beta_series.rolling(period, min_periods=min_periods).mean()
        beta_std = beta_series.rolling(period, min_periods=min_periods).std()
        
        # 计算标准分
        latest_beta = betas[-1]
        if latest_beta is None or pd.isna(beta_mean.iloc[-1]) or pd.isna(beta_std.iloc[-1]) or beta_std.iloc[-1] == 0:
            return None
            
        std_score = (latest_beta - beta_mean.iloc[-1]) / beta_std.iloc[-1]
        return std_score
    except Exception as e:
        logger.error(f"计算RSRS标准分错误: {str(e)}")
        return None

def check(code_name, data, end_date=None):
    """统一的策略入口函数"""
    try:
        if data is None or len(data) < MIN_PERIODS:
            return False
            
        # 检查必要的数据列
        required_columns = ['日期', '最高', '最低', '名称']
        if not all(col in data.columns for col in required_columns):
            logger.error(f"股票 {code_name} 数据缺少必要的列")
            return False
            
        if end_date is not None:
            mask = (data['日期'] <= end_date)
            data = data.loc[mask]
        
        # 计算RSRS标准分
        std_score = calculate_rsrs_std_score(data)
        
        if std_score is None:
            return False
        
        stock_name = data['名称'].iloc[-1] if '名称' in data.columns else ''
        
        # 检查买入和卖出信号
        if std_score > BUY_THRESHOLD:
            logger.info(f"股票 {code_name}-{stock_name} RSRS标准分 {std_score:.2f} > {BUY_THRESHOLD} 产生买入信号")
            return True
        elif std_score < SELL_THRESHOLD:
            logger.info(f"股票 {code_name}-{stock_name} RSRS标准分 {std_score:.2f} < {SELL_THRESHOLD} 产生卖出信号")
            return False
            
        return False
    except Exception as e:
        logger.error(f"检查股票 {code_name} 信号时错误: {str(e)}")
        return False

def check_enter(code_name, data, end_date=None):
    """入场信号检测"""
    try:
        if data is None or len(data) < MIN_PERIODS:
            return False
            
        std_score = calculate_rsrs_std_score(data)
        if std_score is not None and std_score > BUY_THRESHOLD:
            logger.info(f"股票 {code_name} RSRS标准分 {std_score:.2f} > {BUY_THRESHOLD} 产生买入信号")
            return True
            
        return False
    except Exception as e:
        logger.error(f"检查股票 {code_name} 买入信号时错误: {str(e)}")
        return False

def check_exit(code_name, data, end_date=None):
    """退出信号检测"""
    try:
        if data is None or len(data) < MIN_PERIODS:
            return False
            
        std_score = calculate_rsrs_std_score(data)
        if std_score is not None and std_score < SELL_THRESHOLD:
            logger.info(f"股票 {code_name} RSRS标准分 {std_score:.2f} < {SELL_THRESHOLD} 产生卖出信号")
            return True
            
        return False
    except Exception as e:
        logger.error(f"检查股票 {code_name} 卖出信号时错误: {str(e)}")
        return False
