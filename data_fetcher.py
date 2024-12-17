# -*- encoding: UTF-8 -*-

import akshare as ak
import pandas as pd
import time
import os
import traceback
from logger_manager import LoggerManager
from utils import get_stock_info
import random
from colorama import Fore, Style

class DataFetcher:
    """数据获取器"""
    def __init__(self, logger_manager=None):
        # Setup logging using logger_manager
        self.logger_manager = logger_manager if logger_manager is not None else LoggerManager()
        self.logger = self.logger_manager.get_logger("data_fetcher")
        
        # Configuration
        self.cache_dir = 'cache'
        self.cache_duration = 24 * 60 * 60  # 24 hours in seconds
        self.max_retries = 3
        self.retry_delay = 0.01
        self.request_interval = 0.01
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.logger.info("DataFetcher initialized successfully")
    
    def _validate_data(self, df, code):
        """验证获取的数据是否满足要求"""
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
        
    def get_stock_list(self):
        """获取A股列表（已剔除ST、退市、科创板和北交所股票）"""
        try:
            print(f"\n{Fore.CYAN}正在获取A股列表...{Style.RESET_ALL}")
            stock_list = get_stock_info()
            
            if stock_list is None or len(stock_list) == 0:
                print(f"{Fore.RED}获取股票列表失败{Style.RESET_ALL}")
                self.logger.error("Failed to get stock list")
                return None
            
            print(f"{Fore.GREEN}成功获取 {len(stock_list)} 只有效股票{Style.RESET_ALL}")
            self.logger.info(f"Successfully got {len(stock_list)} stocks")
            return stock_list
            
        except Exception as e:
            print(f"{Fore.RED}获取股票列表失败: {str(e)}{Style.RESET_ALL}")
            self.logger.error(f"Error getting stock list: {str(e)}")
            self.logger.error(traceback.format_exc())
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
            
    def get_stock_data(self, stock, data_type='daily'):
        """获取股票数据"""
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
            
            self.logger.info(f"Getting {data_type} data for stock {code}")
            
            # 获取数据
            df = self._fetch_stock_data(code)
            
            if df is not None:
                self.logger.info(f"Successfully retrieved data for {code}")
                return df
            else:
                self.logger.error(f"Failed to retrieve data for {code}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error getting data for {code}: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
            
    def _fetch_stock_data(self, code, retries=0):
        """获取股票日线数据"""
        try:
            if retries > 0:
                time.sleep(self.retry_delay * (2 ** (retries - 1)))
                
            # 检查缓存
            cache_file = os.path.join(self.cache_dir, f"{code}_daily.csv")
            if os.path.exists(cache_file):
                cache_time = os.path.getmtime(cache_file)
                if time.time() - cache_time < self.cache_duration:
                    try:
                        # 检查文件是否为空
                        if os.path.getsize(cache_file) > 0:
                            df = pd.read_csv(cache_file)
                            if not df.empty and 'date' in df.columns:
                                df['date'] = pd.to_datetime(df['date'])
                                df.set_index('date', inplace=True)
                                if self._validate_data(df, code):
                                    self.logger.info(f"Using cached data for {code}")
                                    return df
                        # 如果文件为空或无效，删除缓存文件
                        os.remove(cache_file)
                        self.logger.warning(f"Removed invalid cache file for {code}")
                    except Exception as e:
                        self.logger.error(f"Error reading cache file for {code}: {str(e)}")
                        # 删除损坏的缓存文件
                        os.remove(cache_file)
                        
            # 获取数据
            self.logger.info(f"Fetching data for stock {code}")
            df = ak.stock_zh_a_hist(symbol=code, adjust="qfq")
            
            # 标准化数据
            df = self._standardize_columns(df)
            
            # 验证数据
            if not self._validate_data(df, code):
                raise ValueError("Data validation failed")
                
            # 保存缓存前确保数据有效
            if not df.empty:
                df.to_csv(cache_file)
            
            # 添加随机延时，避免请求过快
            time.sleep(random.uniform(0.5, 1.5))
            
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