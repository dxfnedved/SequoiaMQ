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

# 信号状态
SIGNAL_BUY = "买入"          # 标准分由小于0.7变大超过0.7
SIGNAL_HOLD = "持有"         # 标准分已经大于0.7
SIGNAL_SELL = "卖出"         # 标准分由大于-0.7变小至小于-0.7
SIGNAL_OBSERVE = "观望"      # 标准分已经小于-0.7
SIGNAL_NEUTRAL = "观望"      # 其他情况

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
        return None, None
    
    try:
        # 计算每个窗口的beta值
        betas = []
        for i in range(len(data) - min_periods + 1):
            window_data = data.iloc[i:i+min_periods]
            beta = calculate_beta(window_data)
            if beta is not None:  # 只添加有效的beta值
                betas.append(beta)
            else:
                betas.append(np.nan)  # 使用NaN代替None
        
        # 将前min_periods-1个位置的beta设为NaN
        betas = [np.nan] * (min_periods-1) + betas
        
        # 转换为Series以便计算移动平均和标准差
        beta_series = pd.Series(betas, index=data.index[:len(betas)])
        
        # 使用pandas的rolling方法
        beta_mean = beta_series.rolling(window=period, min_periods=min_periods).mean()
        beta_std = beta_series.rolling(window=period, min_periods=min_periods).std()
        
        # 计算标准分
        latest_beta = beta_series.iloc[-1]
        prev_beta = beta_series.iloc[-2] if len(beta_series) > 1 else np.nan
        
        if pd.isna(latest_beta) or pd.isna(beta_mean.iloc[-1]) or pd.isna(beta_std.iloc[-1]) or beta_std.iloc[-1] == 0:
            return None, None
            
        latest_score = (latest_beta - beta_mean.iloc[-1]) / beta_std.iloc[-1]
        prev_score = (prev_beta - beta_mean.iloc[-2]) / beta_std.iloc[-2] if len(beta_mean) > 1 and len(beta_std) > 1 else None
        
        return latest_score, prev_score
    except Exception as e:
        logger.error(f"计算RSRS标准分错误: {str(e)}")
        return None, None

def determine_signal(latest_score, prev_score):
    """根据当前和前一个标准分确定信号"""
    if latest_score is None:
        return SIGNAL_NEUTRAL
        
    if prev_score is None:
        # 只有当前分数时的判断
        if latest_score > BUY_THRESHOLD:
            return SIGNAL_HOLD
        elif latest_score < SELL_THRESHOLD:
            return SIGNAL_OBSERVE
        else:
            return SIGNAL_NEUTRAL
            
    # 有前后两个分数时的趋势判断
    if latest_score > BUY_THRESHOLD:
        if prev_score <= BUY_THRESHOLD:
            return SIGNAL_BUY  # 突破买入阈值
        else:
            return SIGNAL_HOLD  # 维持在买入阈值以上
    elif latest_score < SELL_THRESHOLD:
        if prev_score >= SELL_THRESHOLD:
            return SIGNAL_SELL  # 突破卖出阈值
        else:
            return SIGNAL_OBSERVE  # 维持在卖出阈值以下
    else:
        return SIGNAL_NEUTRAL

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
        latest_score, prev_score = calculate_rsrs_std_score(data)
        
        if latest_score is None:
            return False
        
        stock_name = data['名称'].iloc[-1] if '名称' in data.columns else ''
        signal = determine_signal(latest_score, prev_score)
        
        # 记录信号
        logger.info(f"股票 {code_name}-{stock_name} RSRS标准分 {latest_score:.2f} "
                   f"产生{signal}信号")
        
        # 只有在首次突破买入阈值时返回True
        return signal == SIGNAL_BUY
        
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
