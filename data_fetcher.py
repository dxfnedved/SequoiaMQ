# -*- encoding: UTF-8 -*-

import akshare as ak
import pandas as pd
import time
import os
import traceback
from logger_manager import LoggerManager
from utils import get_stock_info, is_weekday
import random
from colorama import Fore, Style
from settings import STOCK_DATA_CACHE_DIR, CACHE_DURATION, MAX_RETRIES, RETRY_DELAY, START_DATE, END_DATE
from datetime import datetime

class DataFetcher:
    """数据获取器"""
    def __init__(self, logger_manager=None):
        # Setup logging using logger_manager
        self.logger_manager = logger_manager if logger_manager is not None else LoggerManager()
        self.logger = self.logger_manager.get_logger("data_fetcher")
        
        # Configuration from settings
        self.cache_dir = STOCK_DATA_CACHE_DIR
        self.cache_duration = CACHE_DURATION
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY
        self.request_interval = 0.01
        self.start_date = START_DATE
        self.end_date = END_DATE
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.logger.info("DataFetcher initialized successfully")
    
    def _validate_data(self, df, code):
        """验证获取的数据是否满足要求"""
        try:
            if df is None or df.empty:
                self.logger.error(f"股票 {code} 数据为空")
                return False
                
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                self.logger.error(f"股票 {code} 缺少必要列: {missing_cols}")
                return False
                
            # 检查是否有足够的数据行
            if len(df) < 20:  # 至少需要20个交易日的数据
                self.logger.error(f"股票 {code} 数据行数不足: {len(df)} < 20")
                return False
                
            # 检查每列的有效数据
            for col in required_cols:
                null_count = df[col].isnull().sum()
                zero_count = (df[col] == 0).sum()
                total_rows = len(df)
                
                # 如果超过20%的数据无效（空值或0），则认为数据质量不足
                invalid_ratio = (null_count + zero_count) / total_rows
                if invalid_ratio > 0.2:
                    self.logger.error(f"股票 {code} 列 {col} 的无效数据比例过高: {invalid_ratio:.2%}")
                    return False
                    
            # 检查数据的时间跨度
            if isinstance(df.index, pd.DatetimeIndex):
                date_range = (df.index.max() - df.index.min()).days
                if date_range < 30:  # 至少需要30天的数据
                    self.logger.error(f"股票 {code} 数据时间跨度不足: {date_range} 天 < 30天")
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"验证股票 {code} 数据时出错: {str(e)}")
            return False
            
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
                
            # 设置期索引
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
            # 按日期排序
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"标准化数据列失败: {str(e)}")
            return None
            
    def _is_data_valid(self, data, code):
        """检查数据是否有效且是最新的"""
        try:
            if data is None or data.empty:
                return False
                
            # 获取当前时间
            now = datetime.now()
            current_time = now.time()
            
            # 获取数据的最新日期
            last_date = pd.to_datetime(data.index[-1])
            
            # 如果是交易日
            if is_weekday():
                # 如果当前时间在9:30之前，数据日期应该是上一个交易日
                if current_time < datetime.strptime('09:30', '%H:%M').time():
                    # 数据日期应该是最近的一个交易日
                    return True
                # 如果当前时间在15:00之后，数据日期应该是今天
                elif current_time > datetime.strptime('15:00', '%H:%M').time():
                    return last_date.date() == now.date()
                # 如果在交易时间内，数据应该是实时的
                else:
                    # 检查数据时间是否在合理范围内（允许5分钟延迟）
                    time_diff = (now - last_date).total_seconds() / 60
                    return time_diff <= 5
            else:
                # 非交易日，使用最近一个交易日的数据
                return True
                
        except Exception as e:
            self.logger.error(f"检查数据时效性时出错 {code}: {str(e)}")
            return False
            
    def _fetch_stock_data(self, code, retries=0, start_date=START_DATE, end_date=END_DATE):
        """获取股票日线数据"""
        try:
            if retries > 0:
                time.sleep(self.retry_delay * (2 ** (retries - 1)))
                
            # 获取数据
            self.logger.info(f"从网络获取数据: {code}")
            df = ak.stock_zh_a_hist(symbol=code,start_date=start_date, end_date=end_date, adjust="qfq")
            
            if df is None or df.empty:
                if retries < self.max_retries:
                    self.logger.warning(f"获取股票 {code} 数据为空，尝试重新获取 (重试 {retries + 1}/{self.max_retries})")
                    return self._fetch_stock_data(code, retries + 1, start_date, end_date)
                self.logger.error(f"获取股票 {code} 数据失败，已达到最大重试次数")
                return None
            
            # 标准化数据
            df = self._standardize_columns(df)
            
            # 验证数据
            if not self._validate_data(df, code):
                if retries < self.max_retries:
                    self.logger.warning(f"股票 {code} 数据验证失败，尝试重新获取 (重试 {retries + 1}/{self.max_retries})")
                    time.sleep(random.uniform(1, 3))  # 添加随机延时
                    return self._fetch_stock_data(code, retries + 1)
                self.logger.error(f"股票 {code} 数据验证失败，已达到最大重试次数")
                return None
                
            # 保存缓存前确保数据有效
            if not df.empty:
                cache_file = os.path.join(self.cache_dir, f"{code}_daily.csv")
                df.to_csv(cache_file)
                self.logger.info(f"数据已缓存: {code}")
            
            # 添加随机延时，避免请求过快
            time.sleep(random.uniform(0.5, 1.5))
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取股票 {code} 数据时出错: {str(e)}")
            if retries < self.max_retries:
                self.logger.warning(f"尝试重新获取股票 {code} 数据 (重试 {retries + 1}/{self.max_retries})")
                return self._fetch_stock_data(code, retries + 1)
            return None
            
    def _should_update_data(self, code, cache_file):
        """判断是否需要更新数据"""
        try:
            if not os.path.exists(cache_file):
                return True
                
            # 获取缓存文件的最后修改时间
            cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            current_time = datetime.now()
            
            # 检查是否是工作日
            is_trading_day = is_weekday()
            
            # 如果是工作日
            if is_trading_day:
                current_hour = current_time.hour
                # 如果在交易时间内（9:30-15:00），每5分钟更新一次
                if 9 <= current_hour < 15:
                    return (current_time - cache_time).total_seconds() > 300  # 5分钟
                # 如果是开盘前（9点前），使用上一个交易日的收盘数据
                elif current_hour < 9:
                    return False
                # 如果是收盘后，使用当天的收盘数据
                else:
                    # 如果缓存是在收盘前的数据，需要更新
                    cache_hour = cache_time.hour
                    return cache_hour < 15
            else:
                # 非交易日，使用最近一个交易日的收盘数据
                # 如果缓存是在最近一个交易日15点之后的数据，不需要更新
                last_trading_day = self._get_last_trading_day()
                if last_trading_day:
                    cache_date = cache_time.date()
                    if cache_date == last_trading_day and cache_time.hour >= 15:
                        return False
                return True
                
        except Exception as e:
            self.logger.error(f"检查数据更新状态时出错 {code}: {str(e)}")
            return True
            
    def _get_last_trading_day(self):
        """获取最近的交易日"""
        try:
            # 获取交易日历
            calendar_df = ak.tool_trade_date_hist_sina()
            if calendar_df is None or calendar_df.empty:
                return None
                
            # 获取当前日期
            current_date = datetime.now().date()
            
            # 转换日期格式
            calendar_df['trade_date'] = pd.to_datetime(calendar_df['trade_date']).dt.date
            
            # 获取小于当前日期的最大交易日
            last_trading_day = calendar_df[calendar_df['trade_date'] < current_date]['trade_date'].max()
            
            return last_trading_day
            
        except Exception as e:
            self.logger.error(f"获取最近交易日失败: {str(e)}")
            return None
            
    def get_stock_data(self, stock):
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
            
            self.logger.info(f"获取股票数据: {code}")
            
            # 检查缓存
            cache_file = os.path.join(self.cache_dir, f"{code}_daily.csv")
            
            # 判断是否需要更新数据
            if self._should_update_data(code, cache_file):
                self.logger.info(f"需要更新股票 {code} 的数据")
                # 从网络获取新数据
                df = self._fetch_stock_data(code)
                if df is not None:
                    self.logger.info(f"成功获取股票 {code} 数据")
                    return df
                else:
                    self.logger.error(f"获取股票 {code} 数据失败")
                    # 如果获取失败但存在缓存，尝试使用缓存
                    if os.path.exists(cache_file):
                        self.logger.info(f"尝试使用缓存数据: {code}")
                        df = pd.read_csv(cache_file)
                        if not df.empty and 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'])
                            df.set_index('date', inplace=True)
                            if self._validate_data(df, code):
                                return df
                    return None
            else:
                # 使用缓存数据
                self.logger.info(f"使用缓存数据: {code}")
                df = pd.read_csv(cache_file)
                if not df.empty and 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    if self._validate_data(df, code):
                        return df
                return None
            
        except Exception as e:
            self.logger.error(f"获取股票 {code} 数据时出错: {str(e)}")
            return None