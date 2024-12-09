# -*- encoding: UTF-8 -*-
import logging
import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class LowBacktraceIncreaseStrategy(BaseStrategy):
    """低回撤增长策略"""
    def __init__(self):
        super().__init__()
        self.name = "LowBacktraceIncreaseStrategy"
        self.window_size = 20  # 观察窗口
        self.backtrace_threshold = 0.1  # 回撤阈值
        self.increase_threshold = 0.2  # 增长阈值
        self.ma_window = 20  # 均线周期
        
    def calculate_backtrace(self, data):
        """计算回撤"""
        try:
            close = data['收盘']
            
            # 计算历史最高价
            rolling_max = close.rolling(window=self.window_size).max()
            
            # 计算回撤
            drawdown = (rolling_max - close) / rolling_max
            
            return drawdown
            
        except Exception as e:
            print(f"计算回撤失败: {str(e)}")
            return None
            
    def calculate_increase(self, data):
        """计算增长率"""
        try:
            close = data['收盘']
            
            # 计算增长率
            increase = close.pct_change(periods=self.window_size)
            
            return increase
            
        except Exception as e:
            print(f"计算增长率失败: {str(e)}")
            return None
            
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.window_size:
                return None
                
            # 计算回撤和增长率
            drawdown = self.calculate_backtrace(data)
            increase = self.calculate_increase(data)
            
            if drawdown is None or increase is None:
                return None
                
            # 计算均线
            ma = data['收盘'].rolling(window=self.ma_window).mean()
            
            # 获取最新数据
            latest_close = data['收盘'].iloc[-1]
            latest_drawdown = drawdown.iloc[-1]
            latest_increase = increase.iloc[-1]
            latest_ma = ma.iloc[-1]
            
            # 判断信号
            if (latest_drawdown < self.backtrace_threshold and
                latest_increase > self.increase_threshold and
                latest_close > latest_ma):
                signal = "买入"
            elif latest_drawdown > self.backtrace_threshold * 2:
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'drawdown': latest_drawdown,
                'increase': latest_increase,
                'ma': latest_ma,
                'signal': signal
            }
            
        except Exception as e:
            print(f"低回撤增长策略分析失败: {str(e)}")
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
                    'drawdown': result['drawdown'],
                    'increase': result['increase'],
                    'ma': result['ma']
                })
                
            return signals
            
        except Exception as e:
            print(f"获取低回撤增长策略信号失败: {str(e)}")
            return []
