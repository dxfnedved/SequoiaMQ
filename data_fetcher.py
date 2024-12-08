# -*- encoding: UTF-8 -*-

import akshare as ak
import pandas as pd
import numpy as np
import time
from tqdm import tqdm
import traceback
from loguru import logger

def process_data(df):
    """处理数据，包括类型转换和空值处理"""
    try:
        # 重命名列
        df = df.rename(columns={
            '日期': 'Date', '开盘': 'Open', '收盘': 'Close',
            '最高': 'High', '最低': 'Low', '成交量': 'Volume',
            '成交额': 'Amount', '振幅': 'Amplitude', '涨跌幅': 'Change',
            '涨跌额': 'ChangeAmount', '换手率': 'Turnover'
        })
        
        # 设置日期索引
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        
        # 处理数值列
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Amount', 
                         'Amplitude', 'Change', 'ChangeAmount', 'Turnover']
        
        for col in numeric_columns:
            if col in df.columns:
                # 使用 ffill() 替代 fillna(method='ffill')
                df[col] = df[col].ffill().fillna(0).astype(np.float64)
        
        return df
        
    except Exception as e:
        logger.error(f"数据处理失败: {str(e)}")
        return None

def process_stock_data(df):
    """处理股票数据，统一字段名和计算指标"""
    try:
        if df is None or df.empty:
            return None
            
        # 确保数据类型正确
        df = process_data(df)
        
        # 设置日期索引
        if 'Date' in df.columns:
            df.set_index('Date', inplace=True)
        df.index = pd.to_datetime(df.index)
        
        # 计算涨跌幅（如果不存在）
        if 'Change' not in df.columns:
            df['Change'] = df['Close'].pct_change() * 100
        df['Change'] = df['Change'].fillna(0).astype(np.float64)
        
        # 添加p_change字段（与涨跌幅相同，保持兼容性）
        df['p_change'] = df['Change']
        
        # 计算成交额（如果不存在）
        if 'Amount' not in df.columns:
            df['Amount'] = df['Volume'] * df['Close']
            
        # 计算技术指标
        for period in [5, 10, 20]:
            # 价格均线
            df[f'ma{period}'] = df['Close'].rolling(window=period, min_periods=1).mean()
            # 成交量均线
            df[f'vol_ma{period}'] = df['Volume'].rolling(window=period, min_periods=1).mean()
            
        # 确保所有计算列的类型为float64
        calculated_columns = ['Change', 'p_change', 'Amount'] + \
                           [f'ma{p}' for p in [5, 10, 20]] + \
                           [f'vol_ma{p}' for p in [5, 10, 20]]
        for col in calculated_columns:
            if col in df.columns:
                df[col] = df[col].astype(np.float64)
        
        # 确保所有必要的列都存在
        required_columns = ['Open', 'Close', 'High', 'Low', 'Volume', 'Amount', 'Change', 'p_change']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"缺少必要的列: {missing_columns}")
            return None
        
        # 删除包含NaN的关键数据行
        key_columns = ['Open', 'Close', 'High', 'Low', 'Volume']
        df = df.dropna(subset=key_columns)
        
        # 确保数据按日期排序
        df = df.sort_index()
        
        # 重置其他列的NaN为0
        df = df.fillna(0)
        
        return df
        
    except Exception as e:
        logger.error(f"处理股票数据时出错: {str(e)}\n{traceback.format_exc()}")
        return None

def fetch_stock_data(code, name, retries=3, delay=1):
    """获取单只股票数据"""
    for attempt in range(retries):
        try:
            # 获取日线数据
            df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
            
            if df is None or df.empty:
                logger.warning(f"股票 {code} - {name} 数据为空")
                return None
            
            # 处理数据
            df = process_stock_data(df)
            if df is None:
                logger.warning(f"股票 {code} - {name} 数据处理失败")
                return None
                
            logger.debug(f"股票 {code} - {name} 数据获取成功，列名: {df.columns.tolist()}")
            return df
            
        except Exception as e:
            logger.error(f"获取股票 {code} - {name} 数据失败 (尝试 {attempt + 1}/{retries}): {str(e)}\n{traceback.format_exc()}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None

def run(stocks):
    """获取多只股票数据"""
    if not stocks:
        logger.warning("没有需要获取的股票")
        return {}
        
    logger.info(f"开始获取{len(stocks)}只股票数据...")
    
    results = {}
    success_count = 0
    fail_count = 0
    
    try:
        with tqdm(total=len(stocks), desc="获取数据进度") as pbar:
            for code, name in stocks:
                df = fetch_stock_data(code, name)
                if df is not None:
                    results[code] = df
                    success_count += 1
                else:
                    fail_count += 1
                pbar.update(1)
                
        logger.info(f"数据获取完成：成功{success_count}只，失败{fail_count}只")
        
        if not results:
            logger.error("未能获取到任何股票数据")
        elif fail_count > 0:
            logger.warning(f"部分股票({fail_count}只)数据获取失败")
            
        return results
        
    except Exception as e:
        logger.error(f"获取数据过程出错: {str(e)}\n{traceback.format_exc()}")
        return {}
