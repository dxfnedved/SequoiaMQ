# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class Alpha101Strategy(BaseStrategy):
    """Alpha101策略"""
    def __init__(self):
        super().__init__()
        self.name = "Alpha101Strategy"
        self.window_size = 20  # 计算窗口
        self.alpha1_threshold = 0.3  # Alpha1阈值
        self.alpha2_threshold = 0.2  # Alpha2阈值
        self.alpha3_threshold = -0.3  # Alpha3阈值
        self.alpha4_threshold = -0.25  # Alpha4阈值
        
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
            print(f"计算Alpha1失败: {str(e)}")
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
            print(f"计算Alpha2失败: {str(e)}")
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
            print(f"计算Alpha3失败: {str(e)}")
            return 0
            
    def calculate_alpha4(self, data):
        """Alpha#4: (-1 * Ts_Rank(rank(low), 9))"""
        try:
            low = data['最低']
            
            # 计算9日排序
            ts_rank = low.rolling(window=9).apply(lambda x: pd.Series(x).rank().iloc[-1])
            return -1 * ts_rank.iloc[-1]
            
        except Exception as e:
            print(f"计算Alpha4失败: {str(e)}")
            return 0
            
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.window_size:
                return None
                
            # 计算各个Alpha因子
            alpha1 = self.calculate_alpha1(data)
            alpha2 = self.calculate_alpha2(data)
            alpha3 = self.calculate_alpha3(data)
            alpha4 = self.calculate_alpha4(data)
            
            # 判断信号
            if (alpha1 > self.alpha1_threshold and
                alpha2 > self.alpha2_threshold and
                alpha3 < self.alpha3_threshold and
                alpha4 < self.alpha4_threshold):
                signal = "买入"
            elif (alpha1 < -self.alpha1_threshold and
                  alpha2 < -self.alpha2_threshold and
                  alpha3 > -self.alpha3_threshold and
                  alpha4 > -self.alpha4_threshold):
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'alpha1': alpha1,
                'alpha2': alpha2,
                'alpha3': alpha3,
                'alpha4': alpha4,
                'signal': signal
            }
            
        except Exception as e:
            print(f"Alpha101策略分析失败: {str(e)}")
            return None
            
    def get_signals(self, data):
        """获取买卖信号"""
        try:
            if len(data) < self.window_size:
                return []
                
            signals = []
            result = self.analyze(data)
            
            if result and result['signal'] != "无":
                signals.append({
                    'date': data.index[-1],
                    'type': result['signal'],
                    'strategy': self.name,
                    'price': data['收盘'].iloc[-1],
                    'alpha1': result['alpha1'],
                    'alpha2': result['alpha2'],
                    'alpha3': result['alpha3'],
                    'alpha4': result['alpha4']
                })
                
            return signals
            
        except Exception as e:
            print(f"获取Alpha101策略信号失败: {str(e)}")
            return [] 