# -*- encoding: UTF-8 -*-

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from logger_manager import LoggerManager
import time
import random

class DataFetcher:
    """数据获取类"""
    def __init__(self, logger_manager=None):
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("data_fetcher")
        
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 5  # 基础重试延迟（秒）
        self.request_interval = 1  # 请求间隔（秒）
        
    def get_stock_list(self):
        """获取A股列表"""
        for attempt in range(self.max_retries):
            try:
                # 获取所有A股列表
                stock_info = ak.stock_info_a_code_name()
                
                # 过滤条件
                def is_valid_stock(code, name):
                    # 排除ST股票
                    if 'ST' in name.upper():
                        return False
                    # 排除退市股票
                    if '退' in name:
                        return False
                    # 排除科创板股票
                    if code.startswith('688'):
                        return False
                    # 排除北交所股票
                    if code.startswith('8'):
                        return False
                    # 只保留沪深主板、中小板、创业板
                    return code.startswith(('000', '001', '002', '003', '300', '600', '601', '603', '605'))
                
                # 应用过滤条件
                valid_stocks = stock_info[
                    stock_info.apply(lambda x: is_valid_stock(x['code'], x['name']), axis=1)
                ]
                
                self.logger.info(f"获取到 {len(valid_stocks)} 只有效股票")
                return valid_stocks.to_dict('records')
                
            except Exception as e:
                self.logger.error(f"获取股票列表失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # 指数退避
                    time.sleep(delay)
                else:
                    return []
            
    def get_stock_data(self, code):
        """获取股票历史数据"""
        for attempt in range(self.max_retries):
            try:
                print(f"正在获取股票 {code} 的历史数据...")
                # 获取最近一年的日线数据
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                
                # 格式化日期
                start_date_str = start_date.strftime('%Y%m%d')
                end_date_str = end_date.strftime('%Y%m%d')
                
                # 添加随机延迟，避免请求过于频繁
                time.sleep(self.request_interval + random.uniform(0, 1))
                
                # 使用akshare获取数据
                df = ak.stock_zh_a_hist(symbol=code, start_date=start_date_str, end_date=end_date_str)
                
                # 重命名列（使用英文列名）
                df = df.rename(columns={
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
                })
                
                # 设置日期索引
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                # 数据验证
                required_columns = ['open', 'close', 'high', 'low', 'volume']
                if not all(col in df.columns for col in required_columns):
                    self.logger.error(f"股票 {code} 数据缺少必要列")
                    return None
                    
                # 检查数据是否为空
                if df.empty:
                    self.logger.error(f"股票 {code} 数据为空")
                    return None
                    
                # 检查数据是否包含无效值
                if df[required_columns].isnull().any().any():
                    self.logger.error(f"股票 {code} 数据包含无效值")
                    return None
                    
                print(f"成功获取股票 {code} 的历史数据，共 {len(df)} 条记录")
                return df
                
            except Exception as e:
                error_msg = f"获取股票 {code} 数据失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}"
                print(error_msg)
                self.logger.error(error_msg)
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # 指数退避
                    time.sleep(delay)
                else:
                    return None
