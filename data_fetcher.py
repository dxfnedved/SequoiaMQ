# -*- encoding: UTF-8 -*-

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm
from logger_manager import LoggerManager
import concurrent.futures
import threading
from functools import partial

class DataFetcher:
    """数据获取器类"""
    def __init__(self, logger_manager=None, max_workers=10):
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("data_fetcher")
        self.max_workers = max_workers
        self.lock = threading.Lock()
        self.progress_bar = None

    def process_data(self, df):
        """处理数据，包括类型转换和空值处理"""
        try:
            if df is None or df.empty:
                return None
                
            # 设置日期索引
            df['日期'] = pd.to_datetime(df['日期'])
            df.set_index('日期', inplace=True)
            
            # 处理数值列
            numeric_columns = ['开盘', '最高', '最低', '收盘', '成交量', '成交额', 
                             '振幅', '涨跌幅', '涨跌额', '换手率']
            
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = df[col].ffill().fillna(0).astype(np.float64)
            
            return df
            
        except Exception as e:
            self.logger.error(f"数据处理失败: {str(e)}")
            return None

    def process_stock_data(self, df):
        """处理股票数据，添加技术指标"""
        try:
            if df is None or df.empty:
                return None
                
            # 确保数据类型正确
            df = self.process_data(df)
            
            # 设置日期索引
            if '日期' in df.columns:
                df.set_index('日期', inplace=True)
            df.index = pd.to_datetime(df.index)
            
            # 计算涨跌幅（如果不存在）
            if '涨跌幅' not in df.columns:
                df['涨跌幅'] = df['收盘'].pct_change() * 100
            df['涨跌幅'] = df['涨跌幅'].fillna(0).astype(np.float64)
            
            # 添加p_change字段（与涨跌幅相同，保持兼容性）
            df['p_change'] = df['涨跌幅']
            
            # 计算成交额（如果不存在）
            if '成交额' not in df.columns:
                df['成交额'] = df['成交量'] * df['收盘']
                
            # 计算技术指标
            for period in [5, 10, 20]:
                # 价格均线
                df[f'ma{period}'] = df['收盘'].rolling(window=period, min_periods=1).mean()
                # 成交量均线
                df[f'vol_ma{period}'] = df['成交量'].rolling(window=period, min_periods=1).mean()
                
            # 确保所有计算列的类型为float64
            calculated_columns = ['涨跌幅', 'p_change', '成交额'] + \
                               [f'ma{p}' for p in [5, 10, 20]] + \
                               [f'vol_ma{p}' for p in [5, 10, 20]]
            
            for col in calculated_columns:
                if col in df.columns:
                    df[col] = df[col].astype(np.float64)
            
            # 确保所有必要的列都存在
            required_columns = ['开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅', 'p_change']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"数据缺少必要的列: {missing_columns}")
                return None
            
            # 删除包含NaN的关键数据行
            key_columns = ['开盘', '收盘', '最高', '最低', '成交量']
            df = df.dropna(subset=key_columns)
            
            return df
            
        except Exception as e:
            self.logger.error(f"处理股票数据失败: {str(e)}")
            return None

    def fetch_stock_data(self, stock, start_date=None, end_date=None):
        """获取单只股票的历史数据"""
        try:
            # 处理股票代码（可能是元组或字符串）
            code = stock[0] if isinstance(stock, tuple) else stock
            stock_name = stock[1] if isinstance(stock, tuple) else None
            
            # 如果没有指定日期，默认获取近一年的数据
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
            
            # 获取日线数据
            df = ak.stock_zh_a_hist(symbol=code, start_date=start_date, end_date=end_date, adjust="qfq")
            
            # 处理数据
            df = self.process_stock_data(df)
            
            if df is None or df.empty:
                self.logger.error(f"获取股票 {stock} 数据失败")
                return None
                
            return df
            
        except Exception as e:
            self.logger.error(f"获取股票 {stock} 数据时出错: {str(e)}")
            return None

    def fetch_batch(self, stocks):
        """批量获取股票数据"""
        results = {}
        for stock in stocks:
            try:
                data = self.fetch_stock_data(stock)
                if data is not None:
                    # 使用股票代码作为键（如果是元组，取第一个元素）
                    code = stock[0] if isinstance(stock, tuple) else stock
                    with self.lock:
                        results[code] = data
                        if self.progress_bar:
                            self.progress_bar.update(1)
            except Exception as e:
                self.logger.error(f"获取股票 {stock} 数据失败: {str(e)}")
        return results

    def run(self, stock_list):
        """批量获取股票数据（多线程）"""
        try:
            if not stock_list:
                self.logger.error("股票列表为空")
                return {}
                
            total_stocks = len(stock_list)
            self.logger.info(f"开始获取{total_stocks}只股票数据...")
            
            # 创建进度条
            self.progress_bar = tqdm(total=total_stocks, desc="获取数据进度")
            
            # 将股票列表分成多个批次
            batch_size = max(1, total_stocks // (self.max_workers * 4))
            batches = [stock_list[i:i + batch_size] for i in range(0, len(stock_list), batch_size)]
            
            results = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有批次的任务
                future_to_batch = {executor.submit(self.fetch_batch, batch): batch for batch in batches}
                
                # 收集结果
                for future in concurrent.futures.as_completed(future_to_batch):
                    batch_results = future.result()
                    results.update(batch_results)
            
            self.progress_bar.close()
            self.progress_bar = None
            
            if not results:
                self.logger.error("未能获取到任何股票数据")
            else:
                self.logger.info(f"成功获取 {len(results)} 只股票的数据")
                
            return results
            
        except Exception as e:
            self.logger.error(f"批量获取数据失败: {str(e)}")
            if self.progress_bar:
                self.progress_bar.close()
                self.progress_bar = None
            return {}
