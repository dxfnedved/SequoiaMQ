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
        """Fetch stock data with retry logic"""
        try:
            if retries > 0:
                time.sleep(self.retry_delay * (2 ** (retries - 1)))
            
            self.logger.info(f"Fetching daily data for stock {code}")
            
            # 尝试不同的数据获取方式
            df = None
            try:
                # 首先尝试使用 stock_zh_a_hist
                df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20240101", adjust="qfq")
            except Exception as e1:
                self.logger.warning(f"First attempt failed for {code}: {str(e1)}")
                try:
                    # 如果失败，尝试使用 stock_zh_a_daily
                    df = ak.stock_zh_a_daily(symbol=code, adjust="qfq")
                except Exception as e2:
                    self.logger.warning(f"Second attempt failed for {code}: {str(e2)}")
                    try:
                        # 最后尝试使用 stock_zh_a_hist_min_em
                        df_min = ak.stock_zh_a_hist_min_em(symbol=code, period='60', adjust='qfq')
                        if df_min is not None and not df_min.empty:
                            # 将分钟数据转换为日线数据
                            df = df_min.resample('D').agg({
                                '开盘': 'first',
                                '收盘': 'last',
                                '最高': 'max',
                                '最低': 'min',
                                '成交量': 'sum',
                                '成交额': 'sum'
                            }).dropna()
                    except Exception as e3:
                        self.logger.warning(f"Third attempt failed for {code}: {str(e3)}")
            
            # 验证返回的数据
            if df is None or not isinstance(df, pd.DataFrame) or df.empty:
                self.logger.error(f"Empty data returned for stock {code}")
                if retries < self.max_retries:
                    self.logger.warning(f"Retry {retries + 1} for {code}")
                    return self._fetch_stock_data(code, retries + 1)
                return None
            
            # 确保df是DataFrame并转换
            if not isinstance(df, pd.DataFrame):
                try:
                    df = pd.DataFrame(df)
                except Exception as e:
                    self.logger.error(f"Failed to convert data to DataFrame for {code}: {str(e)}")
                    return None
                
            # 统一列名
            column_map = {
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change_amount',
                '换手率': 'turnover_rate'
            }
            
            # 只重命名存在的列
            rename_dict = {k: v for k, v in column_map.items() if k in df.columns}
            if rename_dict:
                df.rename(columns=rename_dict, inplace=True)
            else:
                self.logger.error(f"No matching columns found for {code}")
                return None
            
            # 处理日期列
            date_col = 'date' if 'date' in df.columns else '日期'
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col])
                df.set_index(date_col, inplace=True)
            else:
                self.logger.error(f"No date column found for {code}")
                return None
            
            # 转换数值列
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
            for col in numeric_cols:
                if col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    except Exception as e:
                        self.logger.error(f"Failed to convert {col} to numeric for {code}: {str(e)}")
                        return None
                    
            # 删除无效数据行
            df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
            
            # 验证数据有效性
            if df.empty:
                self.logger.error(f"No valid data after cleaning for {code}")
                return None
            
            if not self._validate_data(df, code):
                raise ValueError(f"Data validation failed for {code}")
            
            self.logger.info(f"Successfully fetched data for {code}")
            return df
            
        except Exception as e:
            if retries < self.max_retries:
                self.logger.warning(f"Retry {retries + 1} for {code}: {str(e)}")
                return self._fetch_stock_data(code, retries + 1)
            else:
                self.logger.error(f"Failed to fetch data for {code} after {self.max_retries} retries: {str(e)}")
                self.logger.error(traceback.format_exc())
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