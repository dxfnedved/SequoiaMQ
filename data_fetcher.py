# -*- encoding: UTF-8 -*-

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from logger_manager import LoggerManager
import time
import random
import os
import json
from pathlib import Path

class DataFetcher:
    """数据获取类"""
    def __init__(self, logger_manager=None):
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("data_fetcher")
        
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 2  # 基础重试延迟（秒）
        self.request_interval = 0.5  # 请求间隔（秒）
        
        # 缓存配置
        self.cache_dir = 'cache'
        self.cache_duration = 24 * 60 * 60  # 缓存时长（秒）
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _get_cache_path(self, code):
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{code}_daily.json")
        
    def _is_cache_valid(self, cache_path):
        """检查缓存是否有效"""
        if not os.path.exists(cache_path):
            return False
        # 检查缓存是否过期
        cache_time = os.path.getmtime(cache_path)
        return (time.time() - cache_time) < self.cache_duration
        
    def _save_to_cache(self, code, data):
        """保存数据到缓存"""
        try:
            cache_path = self._get_cache_path(code)
            data_dict = {
                'timestamp': time.time(),
                'data': data.reset_index().to_dict(orient='records')
            }
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, ensure_ascii=False, indent=2)
            self.logger.info(f"股票 {code} 数据已缓存")
        except Exception as e:
            self.logger.error(f"保存缓存失败: {str(e)}")
            
    def _load_from_cache(self, code):
        """从缓存加载数据"""
        try:
            cache_path = self._get_cache_path(code)
            if self._is_cache_valid(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                df = pd.DataFrame(cached_data['data'])
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                self.logger.info(f"从缓存加载股票 {code} 数据")
                return df
        except Exception as e:
            self.logger.error(f"读取缓存失败: {str(e)}")
        return None
        
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
            
    def get_stock_data(self, stock):
        """获取股票历史数据"""
        # 处理输入参数
        if isinstance(stock, dict):
            code = stock['code']
        elif isinstance(stock, (list, tuple)):
            code = stock[0]
        else:
            code = str(stock)
            
        # 尝试从缓存加载
        cached_data = self._load_from_cache(code)
        if cached_data is not None:
            return cached_data
            
        last_error = None
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    self.logger.info(f"第{attempt + 1}次尝试获取股票 {code} 的历史数据...")
                else:
                    self.logger.info(f"正在获取股票 {code} 的历史数据...")
                
                # 获取最近一年的日线数据
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                
                # 格式化日期
                start_date_str = start_date.strftime('%Y%m%d')
                end_date_str = end_date.strftime('%Y%m%d')
                
                # 添加随机延迟，避免请求过于频繁
                if attempt > 0:
                    delay = self.retry_delay * (2 ** attempt) + random.uniform(0, 1)
                    self.logger.info(f"等待 {delay:.1f} 秒后重试...")
                    time.sleep(delay)
                else:
                    time.sleep(self.request_interval + random.uniform(0, 0.5))
                
                # 使用akshare获取数据
                df = ak.stock_zh_a_hist(symbol=code, start_date=start_date_str, end_date=end_date_str)
                
                if df is None or df.empty:
                    raise ValueError(f"获取到的数据为空")
                
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
                
                # 数据质量检查
                if not self._validate_data_quality(df, code):
                    last_error = ValueError("数据质量检查未通过")
                    continue
                
                # 保存到缓存
                self._save_to_cache(code, df)
                
                self.logger.info(f"成功获取股票 {code} 的历史数据，共 {len(df)} 条记录")
                return df
                
            except Exception as e:
                last_error = e
                error_msg = f"获取股票 {code} 数据失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}"
                self.logger.error(error_msg)
                
                if attempt < self.max_retries - 1:
                    continue
                    
        if last_error:
            self.logger.error(f"股票 {code} 在 {self.max_retries} 次尝试后仍获取失败: {str(last_error)}")
        return None

    def _validate_data_quality(self, df, code):
        """验证数据质量"""
        try:
            # 检查数据是否为空
            if df.empty:
                self.logger.error(f"股票 {code} 数据为空")
                return False
                
            # 检查必要列是否存在
            required_columns = ['open', 'close', 'high', 'low', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"股票 {code} 数据缺少必要列: {missing_columns}")
                return False
                
            # 检查数据长度（降低要求到20天）
            if len(df) < 20:  # 进一步降低要求
                self.logger.error(f"股票 {code} 数据不足20个交易日")
                return False
                
            # 检查数据是否包含无效值（允许更多缺失）
            null_counts = df[required_columns].isnull().sum()
            max_allowed_nulls = len(df) * 0.2  # 允许20%的缺失值
            if (null_counts > max_allowed_nulls).any():
                self.logger.error(f"股票 {code} 数据包含过多无效值")
                return False
                
            # 检查价格数据是否合理（允许零价格，可能是停牌）
            price_columns = ['open', 'close', 'high', 'low']
            if (df[price_columns] < 0).any().any():
                self.logger.error(f"股票 {code} 包含负价格数据")
                return False
                
            # 检查成交量数据是否合理
            if (df['volume'] < 0).any():
                self.logger.error(f"股票 {code} 包含负成交量数据")
                return False
                
            # 检查最高价是否大于等于最低价（允许更多异常）
            price_errors = (df['high'] < df['low']).sum()
            if price_errors > len(df) * 0.1:  # 允许10%的价格异常
                self.logger.error(f"股票 {code} 最高价小于最低价的情况过多")
                return False
                
            # 检查开盘价和收盘价是否在最高价和最低价之间（允许更多异常）
            price_check = (
                (df['open'] >= df['low']) & 
                (df['open'] <= df['high']) & 
                (df['close'] >= df['low']) & 
                (df['close'] <= df['high'])
            )
            if (~price_check).sum() > len(df) * 0.1:  # 允许10%的价格异常
                self.logger.error(f"股票 {code} 价格数据不一致的情况过多")
                return False
                
            # 添加数据统计日志
            self.logger.info(f"""
股票 {code} 数据质量检查通过:
- 数据条数: {len(df)}
- 缺失值统计: {null_counts.to_dict()}
- 价格异常比例: {price_errors/len(df):.2%}
- 价格区间异常比例: {(~price_check).sum()/len(df):.2%}
            """)
            
            return True
            
        except Exception as e:
            self.logger.error(f"数据质量验证失败: {str(e)}")
            return False
