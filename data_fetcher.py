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
import traceback
import utils

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
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
                self.logger.info(f"创建缓存目录: {self.cache_dir}")
            
            cache_path = self._get_cache_path(code)
            
            # 将DataFrame转换为可序列化的格式
            df_dict = data.reset_index().to_dict(orient='records')
            
            # 处理Timestamp对象
            processed_data = []
            for record in df_dict:
                processed_record = {}
                for key, value in record.items():
                    if isinstance(value, pd.Timestamp):
                        processed_record[key] = value.strftime('%Y-%m-%d')
                    else:
                        processed_record[key] = value
                processed_data.append(processed_record)
            
            data_dict = {
                'timestamp': time.time(),
                'data': processed_data
            }
            
            # 确保目录���在
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"股票 {code} 数据已缓存到: {cache_path}")
            
            # 验证缓存文件
            if not os.path.exists(cache_path):
                raise FileNotFoundError(f"缓存文件未能成功创建: {cache_path}")
            
            # 检查文件大小
            file_size = os.path.getsize(cache_path)
            if file_size == 0:
                raise ValueError(f"缓存文件为空: {cache_path}")
            
            self.logger.info(f"缓存文件大小: {file_size/1024:.2f}KB")
            
        except Exception as e:
            self.logger.error(f"保存缓存失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise
        
    def _load_from_cache(self, code):
        """从缓存加载数据"""
        try:
            cache_path = self._get_cache_path(code)
            
            if not os.path.exists(cache_path):
                self.logger.info(f"缓存文件不存在: {cache_path}")
                return None
            
            if not self._is_cache_valid(cache_path):
                self.logger.info(f"缓存文件已过期: {cache_path}")
                return None
            
            # 检查文件大小
            file_size = os.path.getsize(cache_path)
            if file_size == 0:
                self.logger.error(f"缓存文件为空: {cache_path}")
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # 检查数据结构
            if not isinstance(cached_data, dict) or 'data' not in cached_data:
                self.logger.error(f"缓存文件格式错误: {cache_path}")
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(cached_data['data'])
            if df.empty:
                self.logger.error(f"缓存数据为空: {cache_path}")
                return None
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 验证缓存数据
            if not self._validate_cache_data(df, code):
                self.logger.error(f"缓存数据验证失败: {cache_path}")
                try:
                    os.remove(cache_path)
                    self.logger.info(f"已删除无效的缓存文件: {cache_path}")
                except Exception as e:
                    self.logger.error(f"删除无效缓存文件失败: {str(e)}")
                return None
            
            self.logger.info(f"""
成功从缓存加载股票 {code} 数据:
- 缓存文件: {cache_path}
- 文件大小: {file_size/1024:.2f}KB
- 数据条数: {len(df)}
- 数据范围: {df.index.min().strftime('%Y-%m-%d')} 至 {df.index.max().strftime('%Y-%m-%d')}
        """)
            
            return df
            
        except Exception as e:
            self.logger.error(f"读取缓存失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
        
    def get_stock_list(self):
        """获取股票列表"""
        try:
            self.logger.info("开始获取股票列表...")
            
            # 使用utils模块的过滤方法获取股票列表
            stock_list = utils.get_stock_list()
            
            if not stock_list:
                self.logger.error("获取股票列表失败：返回数据为空")
                return []
            
            # 统计市场分布
            codes = pd.DataFrame(stock_list)
            
            self.logger.info(f"""
表获取成功:
- 总数量: {len(stock_list)}
- 市场分布:
  主板: {len(codes[codes['code'].str.match('^(000|001|600|601)', na=False)])}
  中小板: {len(codes[codes['code'].str.match('^(002|003)', na=False)])}
  创业板: {len(codes[codes['code'].str.match('^300', na=False)])}
        """)
            
            return stock_list
            
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            return []

    def is_market_open(self):
        """检查当前是否是开盘时间"""
        now = datetime.now()
        weekday = now.weekday()
        current_time = now.time()
        
        # 如果是周末，市场关闭
        if weekday >= 5:
            return False
        
        # 定义开盘时间段
        morning_start = datetime.strptime('09:30:00', '%H:%M:%S').time()
        morning_end = datetime.strptime('11:30:00', '%H:%M:%S').time()
        afternoon_start = datetime.strptime('13:00:00', '%H:%M:%S').time()
        afternoon_end = datetime.strptime('15:00:00', '%H:%M:%S').time()
        
        # 检查是否在交易时间段内
        is_morning_session = morning_start <= current_time <= morning_end
        is_afternoon_session = afternoon_start <= current_time <= afternoon_end
        
        return is_morning_session or is_afternoon_session

    def should_update_cache(self, code):
        """检查是否需要更新缓存"""
        cache_path = self._get_cache_path(code)
        
        # 如果缓存文件不存在，需要更新
        if not os.path.exists(cache_path):
            return True
        
        # 如果是开盘时间，需要更新
        if self.is_market_open():
            return True
        
        # 查缓存否过期
        cache_time = os.path.getmtime(cache_path)
        cache_age = time.time() - cache_time
        
        # 如果缓存超过指定时间，需要更新
        if cache_age > self.cache_duration:
            return True
        
        return False

    def get_stock_data(self, stock):
        """获取股票历史数据"""
        try:
            # 处理输入参数
            if isinstance(stock, dict):
                code = stock['code']
            elif isinstance(stock, (list, tuple)):
                code = stock[0]
            else:
                code = str(stock)
                
            self.logger.info(f"开始获取股票 {code} 的数据")
            
            # 检查缓存目录是否存在
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
                self.logger.info(f"创建缓存目录: {self.cache_dir}")
            
            # 检查是否需要更新缓存
            should_update = self.should_update_cache(code)
            if should_update:
                self.logger.info(f"股票 {code} 需要更新数据")
                return self._fetch_and_cache_data(code)
            
            # 尝试从缓存加载
            cached_data = self._load_from_cache(code)
            if cached_data is not None:
                self.logger.info(f"成功从缓存加载股票 {code} 的数据")
                return cached_data
            
            # 如果缓存无效，重新获取数据
            self.logger.info(f"股票 {code} 缓存无效，重新获取数据")
            return self._fetch_and_cache_data(code)
            
        except Exception as e:
            self.logger.error(f"获取股票 {code} 数据时发生错误: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None

    def _fetch_and_cache_data(self, code):
        """获取并缓存数据"""
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"开始获取股票 {code} 的历史数据 (尝试 {attempt + 1}/{max_retries})...")
                
                # 获取最近两年的日线数据，增加数据获取范围
                end_date = datetime.now()
                start_date = end_date - timedelta(days=730)  # 改为两年
                
                # 格式化日期
                start_date_str = start_date.strftime('%Y%m%d')
                end_date_str = end_date.strftime('%Y%m%d')
                
                # 添加随机延迟，避免请求过于频繁
                delay = base_delay * (1 + random.random())
                if attempt > 0:
                    delay = base_delay * (2 ** attempt) + random.random()  # 指数退避
                time.sleep(delay)
                
                # 尝试不同的数据获取方法
                df = None
                error_msgs = []
                
                # 方法1: 使用东方财富主接口
                try:
                    self.logger.info("尝试使用东方财富主接口获取数据...")
                    df = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                          start_date=start_date_str,
                                          end_date=end_date_str, adjust="qfq")
                    
                    if df is not None and not df.empty:
                        # 标准化列名
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
                        
                        # 按日期排序
                        df.sort_index(inplace=True)
                        
                        # 确保所有必要的列都存在
                        required_columns = ['open', 'high', 'low', 'close', 'volume']
                        if all(col in df.columns for col in required_columns):
                            self.logger.info("成功从东方财富主接口获取数据")
                        else:
                            df = None
                            error_msgs.append("数据缺少必要列")
                            
                except Exception as e:
                    error_msgs.append(f"东方财富主接口: {str(e)}")
                    
                # 如果主接口失败，尝试分钟数据接口
                if df is None or df.empty:
                    try:
                        self.logger.info("尝试使用分钟数据接口获取数据...")
                        # 获取分钟数据
                        df_min = ak.stock_zh_a_hist_min_em(symbol=code, period='1', 
                                                          start_date=start_date_str,
                                                          end_date=end_date_str)
                        
                        if df_min is not None and not df_min.empty:
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
                            df = df.rename(columns={
                                '开盘': 'open',
                                '收盘': 'close',
                                '最高': 'high',
                                '最低': 'low',
                                '成交量': 'volume',
                                '成交额': 'amount'
                            })
                            
                            # 计算其他指标
                            df['pct_change'] = df['close'].pct_change() * 100
                            df['change'] = df['close'] - df['close'].shift(1)
                            df['amplitude'] = ((df['high'] - df['low']) / df['close'].shift(1)) * 100
                            df['turnover'] = 0  # 默认换手率
                            
                    except Exception as e:
                        error_msgs.append(f"分钟数据接口: {str(e)}")
                    
                # 如果所有方法都失败
                if df is None or df.empty:
                    self.logger.error(f"所有数据源都获取失败: {'; '.join(error_msgs)}")
                    if attempt < max_retries - 1:
                        continue
                    return None
                
                # 数���质量检查
                if not self._validate_data_quality(df, code):
                    if attempt < max_retries - 1:
                        self.logger.info(f"重试获取股票 {code} 数据...")
                        continue
                    self.logger.error(f"股票 {code} 数据质量检查未通过")
                    return None
                
                # 保存到缓存
                try:
                    self._save_to_cache(code, df)
                    self.logger.info(f"股票 {code} 数据已成功缓存")
                except Exception as e:
                    self.logger.error(f"保存股票 {code} 数据到缓存失败: {str(e)}")
                
                self.logger.info(f"""
成功获取股票 {code} 的历史数据:
- 数据条数: {len(df)}
- 时间范围: {df.index.min().strftime('%Y-%m-%d')} 至 {df.index.max().strftime('%Y-%m-%d')}
- 数据列: {', '.join(df.columns)}
                """)
                return df
                
            except Exception as e:
                self.logger.error(f"获取股票 {code} 数据失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                self.logger.error(traceback.format_exc())
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))  # 指��退避
                else:
                    return None
        
        return None

    def _validate_data_quality(self, data, code):
        """验证数据质量"""
        try:
            # 检查数据是否为空
            if data is None or data.empty:
                self.logger.error(f"股票 {code} 数据为空")
                return False
                
            # 检查必要列是否存在
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                self.logger.error(f"股票 {code} 数据缺少必要列: {missing_columns}")
                return False
                
            # 检查数据长度（至少需要10天数据，放宽标准）
            if len(data) < 10:
                self.logger.error(f"股票 {code} 数据不足10个交易日: {len(data)}天")
                return False
                
            # 检查数据是否包含无效值
            null_counts = data[required_columns].isnull().sum()
            max_allowed_nulls = len(data) * 0.2  # 允许20%的缺失值，放宽标准
            if (null_counts > max_allowed_nulls).any():
                self.logger.error(f"股票 {code} 数据包含过多无效值: {null_counts.to_dict()}")
                return False
                
            # 检查数据的时间范围
            date_range = (data.index.max() - data.index.min()).days
            if date_range < 10:  # 放宽时间跨度要求
                self.logger.error(f"股票 {code} 数据时间跨度不足10天: {date_range}天")
                return False
                
            # 检查数据的连续性
            date_diff = data.index.to_series().diff().dt.days
            max_gap = date_diff.max()
            if max_gap > 15:  # 放宽最大间隔限制到15天
                self.logger.error(f"股票 {code} 数据存在较大缺失，最大间隔: {max_gap}天")
                return False
                
            # 检查价格数据的合理性
            if (data['high'] < data['low']).any():
                self.logger.error(f"股票 {code} 数据存在最高价低于最低价的异常")
                return False
                
            if ((data['open'] > data['high']) | (data['open'] < data['low'])).any():
                self.logger.error(f"股票 {code} 数据存在开盘价超出最高最低价范围的异常")
                return False
                
            if ((data['close'] > data['high']) | (data['close'] < data['low'])).any():
                self.logger.error(f"股票 {code} 数据存在收盘价超出最高最低价范围的异常")
                return False
                
            # 检查成交量数据的合理性
            if (data['volume'] < 0).any():
                self.logger.error(f"股票 {code} 数据存在负成交量")
                return False
                
            # 输出数据统计信息
            self.logger.info(f"""
股票 {code} 数据质量检查通过:
- 数据条数: {len(data)}
- 时间范围: {data.index.min().strftime('%Y-%m-%d')} 至 {data.index.max().strftime('%Y-%m-%d')}
- 数据完整性: {(1 - null_counts.sum()/(len(data)*len(required_columns)))*100:.2f}%
- 最大数据间隔: {max_gap}天
- 价格范围: {data['low'].min():.2f} - {data['high'].max():.2f}
- 成交量范围: {data['volume'].min():.0f} - {data['volume'].max():.0f}
            """)
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证股票 {code} 数据质量时发生错误: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def _validate_cache_data(self, data, code):
        """验证缓存数据的完整性"""
        try:
            # 检查数据是否为空
            if data is None or data.empty:
                self.logger.error(f"股票 {code} 缓存数据为空")
                return False
            
            # 检查必要列是否存在
            required_columns = ['open', 'close', 'high', 'low', 'volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                self.logger.error(f"股票 {code} 缓存数据缺少必要列: {missing_columns}")
                return False
            
            # 检查数据长度（至少需要20天数据）
            if len(data) < 20:
                self.logger.error(f"股票 {code} 缓存数据不足20个交易日")
                return False
            
            # 检查数据是否包含无效值
            null_counts = data[required_columns].isnull().sum()
            max_allowed_nulls = len(data) * 0.1  # 允许10%的缺失值
            if (null_counts > max_allowed_nulls).any():
                self.logger.error(f"股票 {code} 缓存数据包含过多无效值: {null_counts.to_dict()}")
                return False
            
            # 检查数据的时间范围
            today = pd.Timestamp.now().normalize()
            latest_date = data.index.max()
            date_diff = (today - latest_date).days
            
            if date_diff > 5 and self.is_market_open():  # 如果是交易时间，数据不能超过5天
                self.logger.error(f"股票 {code} 缓存数据已过期，最新数据日期: {latest_date.strftime('%Y-%m-%d')}")
                return False
            
            if date_diff > 10:  # 非交易时间，数据不能超过10天
                self.logger.error(f"股票 {code} 缓存数据已过期，最新数据日期: {latest_date.strftime('%Y-%m-%d')}")
                return False
            
            # 检查数据的连续性
            date_diff = data.index.to_series().diff().dt.days
            max_gap = date_diff.max()
            if max_gap > 10:  # 如果数据中有超过10天的缺失
                self.logger.error(f"股票 {code} 缓存数据存在较大缺失，最大间隔: {max_gap}天")
                return False
            
            # 检查价格数据的合理性
            if (data['high'] < data['low']).any():
                self.logger.error(f"股票 {code} 缓存数据存在最高价低于最低价的异常")
                return False
            
            if ((data['open'] > data['high']) | (data['open'] < data['low'])).any():
                self.logger.error(f"股票 {code} 缓存数据存在开盘价超出最高最低价范围的异常")
                return False
            
            if ((data['close'] > data['high']) | (data['close'] < data['low'])).any():
                self.logger.error(f"股票 {code} 缓存数据存在收盘价超出最高最低价范围的异常")
                return False
            
            # 检查成交量数据的合理性
            if (data['volume'] < 0).any():
                self.logger.error(f"股票 {code} 缓存数据存在负成交量")
                return False
            
            self.logger.info(f"""
股票 {code} 缓存数据验证通过:
- 数据条数: {len(data)}
- 数据期范围: {data.index.min().strftime('%Y-%m-%d')} 至 {data.index.max().strftime('%Y-%m-%d')}
- 数据完整性: {(1 - null_counts.sum()/(len(data)*len(required_columns)))*100:.2f}%
- 最大数据间隔: {max_gap}天
- 价格范围: {data['low'].min():.2f} - {data['high'].max():.2f}
- 成交量范围: {data['volume'].min():.0f} - {data['volume'].max():.0f}
        """)
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证缓存数据失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def is_from_cache(self, code):
        """检查数据是否来自缓存"""
        cache_path = self._get_cache_path(code)
        return os.path.exists(cache_path) and not self.should_update_cache(code)
