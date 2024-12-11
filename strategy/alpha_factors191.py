# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy
from logger_manager import LoggerManager
import traceback

class Alpha191Strategy(BaseStrategy):
    """Alpha191策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "Alpha191Strategy"
        self.window_size = 20  # 计算窗口
        self.alpha5_threshold = 0.3  # Alpha5阈值
        self.alpha6_threshold = 0.2  # Alpha6阈值
        self.alpha7_threshold = -0.3  # Alpha7阈值
        self.alpha8_threshold = -0.25  # Alpha8阈值
        
    def calculate_alpha5(self, data):
        """Alpha#5: (-1 * ts_rank(rank(volume), 5))"""
        try:
            volume = data['成交量']
            volume_rank = volume.rank()
            ts_rank = volume_rank.rolling(window=5).apply(
                lambda x: pd.Series(x).rank().iloc[-1], raw=True
            )
            return -1 * ts_rank.iloc[-1]
        except Exception as e:
            print(f"计算Alpha5失败: {str(e)}")
            return 0
            
    def calculate_alpha6(self, data):
        """Alpha#6: (rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap)))))"""
        try:
            open_price = data['开盘']
            close = data['收盘']
            volume = data['成交量']
            amount = data['成交额']
            
            # 计算VWAP
            vwap = amount / volume
            vwap_ma10 = vwap.rolling(window=10).mean()
            
            rank_part1 = (open_price - vwap_ma10).rank()
            rank_part2 = (close - vwap).rank()
            
            return (rank_part1 * (-1 * np.abs(rank_part2))).iloc[-1]
        except Exception as e:
            print(f"计算Alpha6失败: {str(e)}")
            return 0
            
    def calculate_alpha7(self, data):
        """Alpha#7: ((rank(max((vwap - close), 3)) + rank(min((vwap - close), 3))) * rank(delta(volume, 3)))"""
        try:
            close = data['收盘']
            volume = data['成交量']
            amount = data['成交额']
            
            # 计算VWAP
            vwap = amount / volume
            vwap_close_diff = vwap - close
            
            rank_max = vwap_close_diff.rolling(window=3).max().rank()
            rank_min = vwap_close_diff.rolling(window=3).min().rank()
            rank_volume_delta = volume.diff(3).rank()
            
            return ((rank_max + rank_min) * rank_volume_delta).iloc[-1]
        except Exception as e:
            print(f"计算Alpha7失败: {str(e)}")
            return 0
            
    def calculate_alpha8(self, data):
        """Alpha#8: rank(delta(((((high + low) / 2) * 0.2) + (vwap * 0.8)), 4))"""
        try:
            high = data['最高']
            low = data['最低']
            volume = data['成交量']
            amount = data['成交额']
            
            # 计算VWAP
            vwap = amount / volume
            
            # 计算中间价格
            mid_price = (high + low) / 2
            
            # 计算加权价格
            weighted_price = mid_price * 0.2 + vwap * 0.8
            
            # 计算4日差分的排名
            return weighted_price.diff(4).rank().iloc[-1]
        except Exception as e:
            print(f"计算Alpha8失败: {str(e)}")
            return 0
            
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.window_size:
                return None
                
            # 计算各个Alpha因子
            alpha5 = self.calculate_alpha5(data)
            alpha6 = self.calculate_alpha6(data)
            alpha7 = self.calculate_alpha7(data)
            alpha8 = self.calculate_alpha8(data)
            
            # 判断信号
            if (alpha5 > self.alpha5_threshold and
                alpha6 > self.alpha6_threshold and
                alpha7 < self.alpha7_threshold and
                alpha8 < self.alpha8_threshold):
                signal = "买入"
            elif (alpha5 < -self.alpha5_threshold and
                  alpha6 < -self.alpha6_threshold and
                  alpha7 > -self.alpha7_threshold and
                  alpha8 > -self.alpha8_threshold):
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'alpha5': alpha5,
                'alpha6': alpha6,
                'alpha7': alpha7,
                'alpha8': alpha8,
                'signal': signal
            }
            
        except Exception as e:
            print(f"Alpha191策略分析失败: {str(e)}")
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
                    'alpha5': result['alpha5'],
                    'alpha6': result['alpha6'],
                    'alpha7': result['alpha7'],
                    'alpha8': result['alpha8']
                })
                
            return signals
            
        except Exception as e:
            print(f"获取Alpha191策略信号失败: {str(e)}")
            return [] 