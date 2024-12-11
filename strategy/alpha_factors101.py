# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy
from logger_manager import LoggerManager
import traceback

class Alpha101Strategy(BaseStrategy):
    """Alpha101策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "Alpha101Strategy"
        self.window_size = 20  # 计算窗口
        self.alpha1_threshold = 0.3  # Alpha1阈值
        self.alpha2_threshold = 0.2  # Alpha2阈值
        self.alpha3_threshold = -0.3  # Alpha3阈值
        self.alpha4_threshold = -0.25  # Alpha4阈值
        
    def prepare_data(self, data):
        """准备数据"""
        try:
            # 检查数据是否为空
            if data is None or data.empty:
                self.logger.error("输入数据为空")
                return None
                
            # 创建数据副本
            df = data.copy()
            
            # 输出原始数据信息
            self.logger.info("="*50)
            self.logger.info("数据预处理开始")
            self.logger.info(f"原始数据列名: {df.columns.tolist()}")
            self.logger.info(f"原始数据类型:\n{df.dtypes}")
            self.logger.info(f"原始数据前5行:\n{df.head()}")
            self.logger.info(f"原始数据形状: {df.shape}")
            
            # 东方财富数据字段映射
            eastmoney_map = {
                'f51': '开盘', 
                'f52': '收盘',
                'f53': '最高',
                'f54': '最低',
                'f55': '成交量',
                'f56': '成交额',
                'f57': '振幅',
                'f58': '涨跌幅',
                'f59': '涨跌额',
                'f60': '换手率',
                'f61': '日期'
            }
            
            # 检查是否是东方财富��数据格式
            if all(col.startswith('f') for col in df.columns if col != 'date'):
                self.logger.info("检测到东方财富数据格式，进行转换")
                rename_map = {k: v for k, v in eastmoney_map.items() if k in df.columns}
                df = df.rename(columns=rename_map)
                self.logger.info(f"转换后的列名: {df.columns.tolist()}")
                
            # 尝试直接使用原始列名
            required_columns = {'开盘', '最高', '最低', '收盘', '成交量'}
            if all(col in df.columns for col in required_columns):
                self.logger.info("使用原始中文列名")
                return df
                
            # 如果找不到中文列名，尝试英文列名
            eng_columns = {'open', 'high', 'low', 'close', 'volume'}
            if all(col in df.columns for col in eng_columns):
                self.logger.info("使用英文列名")
                column_map = {
                    'open': '开盘',
                    'high': '最高',
                    'low': '最低',
                    'close': '收盘',
                    'volume': '成交量'
                }
                return df.rename(columns=column_map)
                
            # 如果还找不到，尝试更多的列名变体
            column_variants = {
                '开盘': ['open', 'Open', 'OPEN', '开盘价', '开盘', 'open_price', 'OpenPrice', 'open_px', 'f51'],
                '最高': ['high', 'High', 'HIGH', '最高价', '最高', 'high_price', 'HighPrice', 'high_px', 'f53'],
                '最低': ['low', 'Low', 'LOW', '最低价', '最低', 'low_price', 'LowPrice', 'low_px', 'f54'],
                '收盘': ['close', 'Close', 'CLOSE', '收盘价', '收盘', 'close_price', 'ClosePrice', 'close_px', 'f52'],
                '成交量': ['volume', 'Volume', 'VOLUME', '成交量', '成交额', 'vol', 'amount', 'TurnoverVolume', 'trade_volume', 'f55']
            }
            
            # 创建映射字典
            column_map = {}
            missing_columns = []
            
            for std_name, variants in column_variants.items():
                found = False
                for variant in variants:
                    if variant in df.columns:
                        column_map[variant] = std_name
                        found = True
                        self.logger.info(f"找到列 {variant} 映射到 {std_name}")
                        break
                if not found:
                    missing_columns.append(std_name)
                    
            if missing_columns:
                self.logger.error(f"找不到以下列或其变体: {missing_columns}")
                self.logger.error(f"可用的列: {df.columns.tolist()}")
                return None
                
            # 重命名列
            df = df.rename(columns=column_map)
            
            # 确保数据类型正确
            for col in ['开盘', '最高', '最低', '收盘', '成交量']:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    self.logger.info(f"列 {col} 转换为数值类型成功")
                except Exception as e:
                    self.logger.error(f"列 {col} 转换为数值类型失败: {str(e)}")
                    return None
                    
            # 删除包含NaN的行
            original_len = len(df)
            df = df.dropna(subset=['开盘', '最高', '最低', '收盘', '成交量'])
            dropped_rows = original_len - len(df)
            if dropped_rows > 0:
                self.logger.warning(f"删除了 {dropped_rows} 行含有NaN的数据")
                
            # 检查数据长度
            if len(df) < self.window_size:
                self.logger.error(f"有效数据长度不足{self.window_size}个周期")
                return None
                
            # 输出处理后的数据信息
            self.logger.info("="*50)
            self.logger.info("数据预处理完成")
            self.logger.info(f"处理后的列名: {df.columns.tolist()}")
            self.logger.info(f"处理后的数据类型:\n{df.dtypes}")
            self.logger.info(f"处理后的数据前5行:\n{df.head()}")
            self.logger.info(f"处理后的数据形状: {df.shape}")
            self.logger.info("="*50)
            
            # 验证数据的有效性
            self.validate_data(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"准备数据失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
            
    def validate_data(self, df):
        """验证数据的有效性"""
        try:
            # 检查价格的合理性
            price_columns = ['开盘', '最高', '最低', '收盘']
            for col in price_columns:
                min_price = df[col].min()
                max_price = df[col].max()
                if min_price <= 0 or max_price > 10000:
                    self.logger.warning(f"{col}价格范围异常: {min_price} - {max_price}")
                    
            # 检查最高价是否大于等于最低价
            invalid_hl = (df['最高'] < df['最低']).sum()
            if invalid_hl > 0:
                self.logger.warning(f"发现{invalid_hl}条记录最高价小于最低价")
                
            # 检查成交量的合理性
            min_volume = df['成交量'].min()
            if min_volume < 0:
                self.logger.warning(f"发现负的成交量: {min_volume}")
                
            # 检查数据的连续性
            if isinstance(df.index, pd.DatetimeIndex):
                date_diff = df.index.to_series().diff()
                irregular_intervals = date_diff.value_counts()
                if len(irregular_intervals) > 1:
                    self.logger.warning(f"数据时间间隔不规则: {irregular_intervals}")
                    
        except Exception as e:
            self.logger.error(f"数据验证失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            
    def calculate_alpha1(self, data):
        """Alpha#1: (rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)"""
        try:
            returns = data['收盘'].pct_change()
            stddev = returns.rolling(window=20).std()
            close = data['收盘']
            
            # 计算SignedPower部分
            condition = returns < 0
            base = np.where(condition, stddev, close)
            signed_power = np.sign(base) * (np.abs(base) ** 2)
            
            # 计算最近5天内最大值的位置
            rolling_max = pd.Series(signed_power).rolling(window=5).apply(lambda x: x.argmax())
            
            # 归一化到[-1, 1]区间
            alpha = (rolling_max / 4) - 0.5
            return alpha.iloc[-1]
            
        except Exception as e:
            self.logger.error(f"计算Alpha1失败: {str(e)}")
            return 0
            
    def calculate_alpha2(self, data):
        """Alpha#2: (-1 * correlation(rank(delta(log(volume), 2)), rank((close - open) / open), 6))"""
        try:
            volume = data['成交量']
            close = data['收盘']
            open_price = data['开盘']
            
            # 计算log(volume)的2日差分
            delta_log_volume = np.log(volume).diff(2)
            
            # 计算(close - open) / open
            returns_intraday = (close - open_price) / open_price
            
            # 计算6日相关系数
            corr = delta_log_volume.rolling(window=6).corr(returns_intraday)
            return -1 * corr.iloc[-1]
            
        except Exception as e:
            self.logger.error(f"计算Alpha2失败: {str(e)}")
            return 0
            
    def calculate_alpha3(self, data):
        """Alpha#3: (-1 * correlation(rank(open), rank(volume), 10))"""
        try:
            open_price = data['开盘']
            volume = data['成交量']
            
            # 计算10日相关系数
            corr = open_price.rolling(window=10).corr(volume)
            return -1 * corr.iloc[-1]
            
        except Exception as e:
            self.logger.error(f"计算Alpha3失败: {str(e)}")
            return 0
            
    def calculate_alpha4(self, data):
        """Alpha#4: (-1 * Ts_Rank(rank(low), 9))"""
        try:
            low = data['最低']
            
            # 计算9日排序
            ts_rank = low.rolling(window=9).apply(lambda x: pd.Series(x).rank().iloc[-1])
            return -1 * ts_rank.iloc[-1]
            
        except Exception as e:
            self.logger.error(f"计算Alpha4失败: {str(e)}")
            return 0
            
    def analyze(self, data):
        """分析数据"""
        try:
            # 准备数据
            df = self.prepare_data(data)
            if df is None:
                return None
                
            # 计算各个Alpha因子
            alpha1 = self.calculate_alpha1(df)
            alpha2 = self.calculate_alpha2(df)
            alpha3 = self.calculate_alpha3(df)
            alpha4 = self.calculate_alpha4(df)
            
            # 判断信号
            signals = []
            if alpha1 > self.alpha1_threshold:
                signals.append("Alpha1看多")
            elif alpha1 < -self.alpha1_threshold:
                signals.append("Alpha1看空")
                
            if alpha2 > self.alpha2_threshold:
                signals.append("Alpha2看多")
            elif alpha2 < -self.alpha2_threshold:
                signals.append("Alpha2看空")
                
            if alpha3 < self.alpha3_threshold:
                signals.append("Alpha3看多")
            elif alpha3 > -self.alpha3_threshold:
                signals.append("Alpha3看空")
                
            if alpha4 < self.alpha4_threshold:
                signals.append("Alpha4看多")
            elif alpha4 > -self.alpha4_threshold:
                signals.append("Alpha4看空")
                
            return {
                'Alpha101Strategy_Alpha1': round(alpha1, 4),
                'Alpha101Strategy_Alpha2': round(alpha2, 4),
                'Alpha101Strategy_Alpha3': round(alpha3, 4),
                'Alpha101Strategy_Alpha4': round(alpha4, 4),
                'Alpha101Strategy_Alpha101_信号': '; '.join(signals) if signals else "无"
            }
            
        except Exception as e:
            self.logger.error(f"Alpha101策略分析失败: {str(e)}")
            return None
            
    def get_signals(self, data):
        """获取买卖信号"""
        try:
            result = self.analyze(data)
            if not result:
                return []
                
            signals = []
            signal_text = result['Alpha101Strategy_Alpha101_信号']
            
            # 统计看多和看空信号的数量
            bullish_count = signal_text.count('看多')
            bearish_count = signal_text.count('看空')
            
            # 根据信号数量生成买卖信号
            if bullish_count >= 2:  # 至少2个看多信号
                signals.append({
                    'date': data.index[-1],
                    'type': '买入',
                    'strategy': 'Alpha101策略',
                    'price': data['收盘'].iloc[-1],
                    'reason': f"Alpha101多头共振({bullish_count}个看多信号)",
                    'strength': bullish_count,  # 信号强度
                    'marker': 'o',  # 圆形标记
                    'color': 'red'  # 红色
                })
            elif bearish_count >= 2:  # 至少2个看空信号
                signals.append({
                    'date': data.index[-1],
                    'type': '卖出',
                    'strategy': 'Alpha101策略',
                    'price': data['收盘'].iloc[-1],
                    'reason': f"Alpha101空头共振({bearish_count}个看空信号)",
                    'strength': bearish_count,
                    'marker': 'o',  # 圆形标记
                    'color': 'red'  # 红色
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取Alpha101策略信号失败: {str(e)}")
            return [] 