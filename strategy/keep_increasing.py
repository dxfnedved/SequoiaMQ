# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class KeepIncreasingStrategy(BaseStrategy):
    """持续上涨策略"""
    def __init__(self):
        super().__init__()
        self.name = "KeepIncreasingStrategy"
        self.window_size = 20  # 观察窗口
        self.min_increase_days = 15  # 最小上涨天数
        self.max_decrease_days = 5  # 最大下跌天数
        self.min_increase_ratio = 0.2  # 最小涨幅
        self.max_decrease_ratio = 0.05  # 最大跌幅
        
    def calculate_trend(self, data):
        """计算趋势"""
        try:
            close = data['收盘']
            
            # 计算日涨跌幅
            daily_returns = close.pct_change()
            
            # 计算上涨和下跌天数
            increase_days = (daily_returns > 0).rolling(window=self.window_size).sum()
            decrease_days = (daily_returns < 0).rolling(window=self.window_size).sum()
            
            # 计算区间涨跌幅
            period_returns = close.pct_change(periods=self.window_size)
            
            # 计算最大回撤
            rolling_max = close.rolling(window=self.window_size).max()
            drawdown = (rolling_max - close) / rolling_max
            max_drawdown = drawdown.rolling(window=self.window_size).max()
            
            return increase_days, decrease_days, period_returns, max_drawdown
            
        except Exception as e:
            print(f"计算趋势失败: {str(e)}")
            return None, None, None, None
            
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.window_size:
                return None
                
            # 计算趋势指标
            increase_days, decrease_days, period_returns, max_drawdown = self.calculate_trend(data)
            
            if any(x is None for x in [increase_days, decrease_days, period_returns, max_drawdown]):
                return None
                
            # 获取最新数据
            latest_increase_days = increase_days.iloc[-1]
            latest_decrease_days = decrease_days.iloc[-1]
            latest_returns = period_returns.iloc[-1]
            latest_max_drawdown = max_drawdown.iloc[-1]
            
            # 判断信号
            if (latest_increase_days >= self.min_increase_days and
                latest_decrease_days <= self.max_decrease_days and
                latest_returns >= self.min_increase_ratio and
                latest_max_drawdown <= self.max_decrease_ratio):
                signal = "买入"
            elif (latest_increase_days < self.min_increase_days / 2 or
                  latest_decrease_days > self.max_decrease_days * 2 or
                  latest_max_drawdown > self.max_decrease_ratio * 2):
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'increase_days': latest_increase_days,
                'decrease_days': latest_decrease_days,
                'period_returns': latest_returns,
                'max_drawdown': latest_max_drawdown,
                'signal': signal
            }
            
        except Exception as e:
            print(f"持续上涨策略分析失败: {str(e)}")
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
                    'increase_days': result['increase_days'],
                    'decrease_days': result['decrease_days'],
                    'period_returns': result['period_returns'],
                    'max_drawdown': result['max_drawdown']
                })
                
            return signals
            
        except Exception as e:
            print(f"获取持续上涨策略信号失败: {str(e)}")
            return []

