# -*- coding: UTF-8 -*-

# 总市值
BALANCE = 200000

import numpy as np
import pandas as pd
from strategy.base import BaseStrategy

class TurtleStrategy(BaseStrategy):
    """海龟交易策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "TurtleStrategy"
        self.window_size = 20  # N日突破
        self.atr_window = 20   # ATR周期
        self.risk_ratio = 0.01 # 风险系数
        
    def calculate_atr(self, data):
        """计算ATR"""
        high = data['最高']
        low = data['最低']
        close = data['收盘']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
        atr = tr.rolling(window=self.atr_window).mean()
        
        return atr
        
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.window_size:
                return None
                
            # 计算N日最高价和最低价
            high_n = data['最高'].rolling(window=self.window_size).max()
            low_n = data['最低'].rolling(window=self.window_size).min()
            
            # 计算ATR
            atr = self.calculate_atr(data)
            
            # 获取最新数据
            latest_price = data['收盘'].iloc[-1]
            latest_high_n = high_n.iloc[-1]
            latest_low_n = low_n.iloc[-1]
            latest_atr = atr.iloc[-1]
            
            # 计算仓位大小
            position_size = self.risk_ratio * latest_price / latest_atr if latest_atr > 0 else 0
            
            # 判断突破
            if latest_price > latest_high_n:
                signal = "买入"
            elif latest_price < latest_low_n:
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'high_n': latest_high_n,
                'low_n': latest_low_n,
                'atr': latest_atr,
                'position_size': position_size,
                'signal': signal
            }
            
        except Exception as e:
            print(f"海龟策略分析失败: {str(e)}")
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
                    'atr': result['atr'],
                    'position_size': result['position_size']
                })
                
            return signals
            
        except Exception as e:
            print(f"获取海龟策略信号失败: {str(e)}")
            return []

__all__ = ['TurtleStrategy']
