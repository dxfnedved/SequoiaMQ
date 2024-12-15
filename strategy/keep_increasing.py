# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class KeepIncreasingStrategy(BaseStrategy):
    """持续上涨策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "KeepIncreasingStrategy"
        self.window_size = 20  # 观察窗口
        self.min_increase_days = 15  # 最小上涨天数
        self.max_decrease_days = 5  # 最大下跌天数
        self.min_increase_ratio = 0.2  # 最小涨幅
        self.max_decrease_ratio = 0.05  # 最大跌幅
        
    def calculate_trend(self, data):
        """计算趋势"""
        try:
            close = data['close']
            
            # 计算每日涨跌
            daily_change = close.pct_change()
            
            # 计算上涨天数和下跌天数
            increase_days = sum(daily_change > 0)
            decrease_days = sum(daily_change < 0)
            
            # 计算总涨幅和总跌幅
            total_increase = daily_change[daily_change > 0].sum()
            total_decrease = abs(daily_change[daily_change < 0].sum())
            
            return increase_days, decrease_days, total_increase, total_decrease
            
        except Exception as e:
            self.logger.error(f"计算趋势失败: {str(e)}")
            return None, None, None, None
            
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.window_size:
                return None
                
            # 获取最近window_size天的数据
            recent_data = data.tail(self.window_size)
            
            # 计算趋势指标
            increase_days, decrease_days, total_increase, total_decrease = self.calculate_trend(recent_data)
            
            if any(x is None for x in [increase_days, decrease_days, total_increase, total_decrease]):
                return None
                
            # 判断信号
            if (increase_days >= self.min_increase_days and
                decrease_days <= self.max_decrease_days and
                total_increase >= self.min_increase_ratio and
                total_decrease <= self.max_decrease_ratio):
                signal = "买入"
            elif decrease_days > self.max_decrease_days or total_decrease > self.max_decrease_ratio:
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'increase_days': increase_days,
                'decrease_days': decrease_days,
                'total_increase': total_increase,
                'total_decrease': total_decrease,
                'signal': signal
            }
            
        except Exception as e:
            self.logger.error(f"持续上涨策略分析失败: {str(e)}")
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
                    'price': data['close'].iloc[-1],
                    'increase_days': result['increase_days'],
                    'decrease_days': result['decrease_days'],
                    'total_increase': result['total_increase'],
                    'total_decrease': result['total_decrease']
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取持续上涨策略信号失败: {str(e)}")
            return []

