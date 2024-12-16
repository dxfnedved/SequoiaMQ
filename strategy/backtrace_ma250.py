# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class BacktraceMA250Strategy(BaseStrategy):
    """回踩年线策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "BacktraceMA250Strategy"
        self.ma_window = 250  # 均线周期
        self.backtrace_threshold = 0.02  # 回踩阈值
        self.volume_ratio = 1.5  # 成交量放大倍数
        self.rsi_threshold = 50  # RSI阈值
        
    def calculate_indicators(self, data):
        """计算技术指标"""
        try:
            # 确保数据是DataFrame格式
            if not isinstance(data, pd.DataFrame):
                self.logger.error("Input data must be a pandas DataFrame")
                return None, None, None, None
            
            # 计算MA250
            close_series = pd.Series(data['close'], index=data.index)
            ma250 = close_series.rolling(window=self.ma_window).mean()
            
            # 计算偏离度
            deviation = (close_series - ma250) / ma250
            
            # 计算成交量比率
            volume_series = pd.Series(data['volume'], index=data.index)
            volume_ma = volume_series.rolling(window=20).mean()
            volume_ratio = volume_series / volume_ma
            
            # 计算RSI
            rsi_values = ta.RSI(close_series.values, timeperiod=14)
            rsi = pd.Series(rsi_values, index=data.index)
            
            return ma250, deviation, volume_ratio, rsi
            
        except Exception as e:
            self.logger.error(f"计算技术指标失败: {str(e)}")
            return None, None, None, None
            
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.ma_window:
                return None
                
            # 计算技术指标
            ma250, deviation, volume_ratio, rsi = self.calculate_indicators(data)
            
            if any(x is None for x in [ma250, deviation, volume_ratio, rsi]):
                return None
                
            # 获取最新数据
            latest_close = data['close'].iloc[-1]
            latest_ma250 = ma250.iloc[-1]
            latest_deviation = deviation.iloc[-1]
            latest_volume_ratio = volume_ratio.iloc[-1]
            latest_rsi = rsi.iloc[-1]
            
            # 判断信号
            if (abs(latest_deviation) < self.backtrace_threshold and
                latest_close > latest_ma250 and
                latest_volume_ratio > self.volume_ratio and
                latest_rsi < self.rsi_threshold):
                signal = "买入"
            elif latest_close < latest_ma250 * 0.95:
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'ma250': latest_ma250,
                'deviation': latest_deviation,
                'volume_ratio': latest_volume_ratio,
                'rsi': latest_rsi,
                'signal': signal
            }
            
        except Exception as e:
            self.logger.error(f"回踩年线策略分析失败: {str(e)}")
            return None
            
    def get_signals(self, data):
        """获取买卖信号"""
        try:
            if len(data) < self.ma_window:
                return []
                
            signals = []
            result = self.analyze(data)
            
            if result and result['signal'] != "无":
                signals.append({
                    'date': data.index[-1],
                    'type': result['signal'],
                    'strategy': self.name,
                    'price': data['close'].iloc[-1],
                    'ma250': result['ma250'],
                    'deviation': result['deviation'],
                    'volume_ratio': result['volume_ratio'],
                    'rsi': result['rsi']
                })
                
            return signals
            
        except Exception as e:
            print(f"获取回踩年线策略信号失败: {str(e)}")
            return []

