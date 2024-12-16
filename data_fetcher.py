# -*- encoding: UTF-8 -*-

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import json
import traceback
from pathlib import Path
from logger_manager import LoggerManager
from utils import is_stock_active
import random

class DataFetcher:
    def __init__(self, logger_manager=None):
        # Setup logging using logger_manager
        self.logger_manager = logger_manager if logger_manager is not None else LoggerManager()
        self.logger = self.logger_manager.get_logger("data_fetcher")
        
        # Configuration
        self.cache_dir = 'cache'
        self.cache_duration = 24 * 60 * 60  # 24 hours in seconds
        self.max_retries = 3
        self.retry_delay = 2
        self.request_interval = 0.5
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.logger.info("DataFetcher initialized successfully")
    
    def _validate_data(self, df, code):
        """Validate fetched data meets requirements"""
        if df is None or df.empty:
            self.logger.error(f"Empty data for stock {code}")
            return False
            
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            self.logger.error(f"Missing columns for {code}: {missing_cols}")
            return False
            
        # Only check for null values
        for col in required_cols:
            if df[col].isnull().all():  # Changed from .any() to .all()
                self.logger.error(f"All values are null in {col} for {code}")
                return False
                
        return True
    
    def _fetch_stock_data(self, code, retries=0):
        """获取股票数据"""
        try:
            if retries > 0:
                time.sleep(self.retry_delay * (2 ** (retries - 1)))
            
            self.logger.info(f"获取股票 {code} 的历史数据")
            
            # 设置时间范围为一年
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            # 格式化日期
            start_date_str = start_date.strftime('%Y%m%d')
            end_date_str = end_date.strftime('%Y%m%d')
            
            # 添加随机延迟，避免请求过于频繁
            delay = random.uniform(0.1, 0.5)
            time.sleep(delay)
            
            # 尝试不同的数据获取方式
            df = None
            error_msgs = []
            
            # 方法1: 使用主接口
            try:
                self.logger.info("尝试使用主接口获取数据...")
                df = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                      start_date=start_date_str,
                                      end_date=end_date_str, adjust="qfq")
                
                if df is not None and not df.empty:
                    df = self._standardize_columns(df)
                    if self._validate_data(df, code):
                        self.logger.info("成功从主接口获取数据")
                        return df
                        
            except Exception as e:
                error_msgs.append(f"主接口: {str(e)}")
                
            # 方法2: 使用分钟数据接口
            try:
                if df is None or df.empty:
                    self.logger.info("尝试使用分钟数据接口...")
                    df_min = ak.stock_zh_a_hist_min_em(symbol=code, period='60',
                                                      start_date=start_date_str,
                                                      end_date=end_date_str)
                    
                    if df_min is not None and not df_min.empty:
                        df = self._convert_min_to_daily(df_min)
                        if df is not None and self._validate_data(df, code):
                            self.logger.info("成功从分钟数据接口获取数据")
                            return df
                            
            except Exception as e:
                error_msgs.append(f"分钟数据接口: {str(e)}")
                
            # 所有方法都失败
            if error_msgs:
                error_msg = "; ".join(error_msgs)
                self.logger.error(f"所有数据源都获取失败: {error_msg}")
                
            if retries < self.max_retries - 1:
                self.logger.info(f"重试获取股票 {code} 数据...")
                return self._fetch_stock_data(code, retries + 1)
                
            return None
            
        except Exception as e:
            self.logger.error(f"获取股票 {code} 数据失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            if retries < self.max_retries - 1:
                return self._fetch_stock_data(code, retries + 1)
            return None
            
    def _standardize_columns(self, df):
        """标准化数据列名"""
        try:
            # 统一列名映射
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
                
            # 按日期排序
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"标准化数据列失败: {str(e)}")
            return None
            
    def _convert_min_to_daily(self, df_min):
        """将分钟数据转换为日线数据"""
        try:
            # 确保时间列是datetime类型
            df_min['时间'] = pd.to_datetime(df_min['时间'])
            
            # 转换为日线数据
            df = df_min.resample('D', on='时间').agg({
                '开盘': 'first',
                '收盘': 'last',
                '最高': 'max',
                '最低': 'min',
                '成交量': 'sum',
                '成交额': 'sum'
            }).dropna()
            
            # 标准化列名
            return self._standardize_columns(df)
            
        except Exception as e:
            self.logger.error(f"转换分钟数据失败: {str(e)}")
            return None
    
    def _fetch_minute_data(self, code, retries=0):
        """Fetch minute-level data with retry logic"""
        try:
            if retries > 0:
                time.sleep(self.retry_delay * (2 ** (retries - 1)))
            
            self.logger.info(f"Fetching minute data for stock {code}")
            df = ak.stock_zh_a_minute(symbol=code, period='60', start_date="20240101", adjust='qfq')
            
            # Rename columns to English
            column_map = {
                '时间': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            }
            df.rename(columns=column_map, inplace=True)
            
            # Convert date and set index
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Convert numeric columns
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            if not self._validate_data(df, code):
                raise ValueError("Data validation failed")
            
            self.logger.info(f"Successfully fetched minute data for {code}")
            return df
            
        except Exception as e:
            if retries < self.max_retries:
                self.logger.warning(f"Retry {retries + 1} for minute data {code}: {str(e)}")
                return self._fetch_minute_data(code, retries + 1)
            else:
                self.logger.error(f"Failed to fetch minute data for {code} after {self.max_retries} retries: {str(e)}")
                self.logger.error(traceback.format_exc())
                return None
    
    def get_stock_data(self, stock, data_type='daily'):
        """Get stock data with validation"""
        try:
            # Extract stock code and name
            if isinstance(stock, dict):
                code = stock['code']
                name = stock.get('name')
            elif isinstance(stock, (list, tuple)):
                code = stock[0]
                name = stock[1] if len(stock) > 1 else None
            else:
                code = str(stock)
                name = None
            
            # 验证股票是否可交易
            if not is_stock_active(code, name):
                self.logger.error(f"股票 {code} 已不再交易")
                return None
            
            self.logger.info(f"Getting {data_type} data for stock {code}")
            
            # Fetch data based on type
            if data_type == 'daily':
                df = self._fetch_stock_data(code)
            else:
                df = self._fetch_minute_data(code)
            
            if df is not None:
                self.logger.info(f"Successfully retrieved {data_type} data for {code}")
                return df
            else:
                self.logger.error(f"Failed to retrieve {data_type} data for {code}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error getting {data_type} data for {code}: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
    
    def get_stock_list(self):
        """Get list of all available stocks"""
        try:
            self.logger.info("Fetching stock list...")
            df = ak.stock_zh_a_spot_em()
            
            stocks = []
            for _, row in df.iterrows():
                code = row['代码']
                name = row['名称']
                
                # 验证股票是否可交易
                if is_stock_active(code, name):
                    stock = {
                        'code': code,
                        'name': name,
                        'market': self._get_market_type(code)
                    }
                    stocks.append(stock)
            
            self.logger.info(f"Retrieved {len(stocks)} valid stocks")
            return stocks
            
        except Exception as e:
            self.logger.error(f"Failed to get stock list: {str(e)}")
            self.logger.error(traceback.format_exc())
            return []
    
    def _get_market_type(self, code):
        """Determine market type from stock code"""
        if code.startswith(('000', '001', '600', '601', '603')):
            return 'main'
        elif code.startswith(('002', '003')):
            return 'sme'
        elif code.startswith('300'):
            return 'gem'
        else:
            return 'other'
    
    def is_market_open(self):
        """Check if market is currently open"""
        now = datetime.now()
        
        # Check weekday
        if now.weekday() >= 5:
            return False
        
        # Check time
        current_time = now.time()
        morning_session = (
            datetime.strptime('09:30:00', '%H:%M:%S').time() <= current_time <=
            datetime.strptime('11:30:00', '%H:%M:%S').time()
        )
        afternoon_session = (
            datetime.strptime('13:00:00', '%H:%M:%S').time() <= current_time <=
            datetime.strptime('15:00:00', '%H:%M:%S').time()
        )
        
        return morning_session or afternoon_session

    def is_from_cache(self, code):
        """Check if data for given stock was retrieved from cache"""
        cache_file = os.path.join(self.cache_dir, f"{code}_daily.json")
        if not os.path.exists(cache_file):
            return False
            
        # Check if cache is still valid
        cache_time = os.path.getmtime(cache_file)
        current_time = time.time()
        return (current_time - cache_time) < self.cache_duration