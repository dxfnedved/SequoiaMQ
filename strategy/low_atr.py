# -*- encoding: UTF-8 -*-
import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class LowATRStrategy(BaseStrategy):
    """低波动策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "LowATRStrategy"
        self.atr_window = 14  # ATR计算周期
        self.ma_window = 20   # 均线周期
        self.atr_threshold = 0.02  # ATR阈值
        self.volume_ratio = 1.5  # 成交量放大倍数
        
    def calculate_atr(self, data):
        """计算ATR"""
        try:
            high = data['最高']
            low = data['最低']
            close = data['收盘']
            
            # 计算TR
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
            
            # 计算ATR
            atr = tr.rolling(window=self.atr_window).mean()
            
            # 计算ATR比率
            atr_ratio = atr / close
            
            return atr, atr_ratio
            
        except Exception as e:
            print(f"计算ATR失败: {str(e)}")
            return None, None
            
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < max(self.atr_window, self.ma_window):
                return None
                
            # 计算ATR
            atr, atr_ratio = self.calculate_atr(data)
            if atr is None or atr_ratio is None:
                return None
                
            # 计算均线
            ma20 = data['收盘'].rolling(window=self.ma_window).mean()
            
            # 获取最新数据
            latest_close = data['收盘'].iloc[-1]
            latest_atr_ratio = atr_ratio.iloc[-1]
            latest_ma20 = ma20.iloc[-1]
            
            # 计算成交量比率
            volume_ma = data['成交量'].rolling(window=self.ma_window).mean()
            volume_ratio = data['成交量'].iloc[-1] / volume_ma.iloc[-1]
            
            # 判断信号
            if (latest_atr_ratio < self.atr_threshold and
                latest_close > latest_ma20 and
                volume_ratio > self.volume_ratio):
                signal = "买入"
            elif latest_atr_ratio > self.atr_threshold * 2:
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'atr': atr.iloc[-1],
                'atr_ratio': latest_atr_ratio,
                'ma20': latest_ma20,
                'volume_ratio': volume_ratio,
                'signal': signal
            }
            
        except Exception as e:
            print(f"低波动策略分析失败: {str(e)}")
            return None
            
    def get_signals(self, data):
        """获取买卖信号"""
        try:
            if len(data) < max(self.atr_window, self.ma_window):
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
                    'atr_ratio': result['atr_ratio'],
                    'ma20': result['ma20'],
                    'volume_ratio': result['volume_ratio']
                })
                
            return signals
            
        except Exception as e:
            print(f"获取低波动策略信号失败: {str(e)}")
            return []
