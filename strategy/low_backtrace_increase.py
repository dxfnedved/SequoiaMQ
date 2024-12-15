# -*- encoding: UTF-8 -*-
import logging
import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class LowBacktraceIncreaseStrategy(BaseStrategy):
    """低回撤上涨策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "LowBacktraceIncreaseStrategy"
        self.window_size = 20  # 观察窗口
        self.ma_window = 20  # 均线周期
        self.min_increase = 0.1  # 最小涨幅
        self.max_backtrace = 0.05  # 最大回撤
        
    def calculate_increase(self, data):
        """计算涨幅"""
        try:
            close = data['close']
            
            # 计算历史最高价
            high_price = close.expanding().max()
            
            # 计算回撤
            backtrace = (high_price - close) / high_price
            
            # 计算总涨幅
            total_increase = close.iloc[-1] / close.iloc[0] - 1
            
            return total_increase, backtrace.max()
            
        except Exception as e:
            self.logger.error(f"计算涨幅失败: {str(e)}")
            return None, None
            
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.window_size:
                return None
                
            # 获取最近window_size天的数据
            recent_data = data.tail(self.window_size)
            
            # 计算涨幅和回撤
            close = data['close']
            increase, max_backtrace = self.calculate_increase(recent_data)
            
            if increase is None or max_backtrace is None:
                return None
                
            # 计算均线
            ma = data['close'].rolling(window=self.ma_window).mean()
            
            # 获取最新数据
            latest_close = data['close'].iloc[-1]
            latest_ma = ma.iloc[-1]
            
            # 判断信号
            if (increase >= self.min_increase and
                max_backtrace <= self.max_backtrace and
                latest_close > latest_ma):
                signal = "买入"
            elif max_backtrace > self.max_backtrace * 2:
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'increase': increase,
                'max_backtrace': max_backtrace,
                'ma': latest_ma,
                'signal': signal
            }
            
        except Exception as e:
            self.logger.error(f"低回撤上涨策略分析失败: {str(e)}")
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
                    'increase': result['increase'],
                    'max_backtrace': result['max_backtrace'],
                    'ma': result['ma']
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取低回撤上涨策略信号失败: {str(e)}")
            return []
