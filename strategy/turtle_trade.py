# -*- coding: UTF-8 -*-

import numpy as np
import pandas as pd
from strategy.base import BaseStrategy

class TurtleStrategy(BaseStrategy):
    """海龟交易策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "TurtleStrategy"
        # 系统1参数（短期系统）
        self.sys1_window = 10  # 缩短系统1的N日突破周期
        self.sys1_exit_window = 5  # 缩短系统1的退出周期
        # 系统2参数（长期系统）
        self.sys2_window = 30  # 缩短系统2的N日突破周期
        self.sys2_exit_window = 15  # 缩短系统2的退出周期
        # 通用参数
        self.atr_window = 14   # 缩短ATR周期
        self.risk_ratio = 0.02  # 提高风险系数
        self.max_units = 4     # 最大加仓次数
        self.stop_loss_atr = 1.5  # 降低止损的ATR倍数
        
    def calculate_atr(self, data):
        """计算ATR"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
        atr = tr.rolling(window=self.atr_window).mean()
        
        return atr
        
    def calculate_position_size(self, price, atr, account_size=1000000):
        """计算仓位大小"""
        if atr == 0:
            return 0
        dollar_volatility = atr
        position_size = (account_size * self.risk_ratio) / dollar_volatility
        return int(position_size)
        
    def check_stop_loss(self, data, entry_price, atr):
        """检查止损条件"""
        current_price = data['close'].iloc[-1]
        stop_loss_price = entry_price - (self.stop_loss_atr * atr)
        return current_price < stop_loss_price
        
    def analyze_system(self, data, window, exit_window):
        """分析单个系统的信号"""
        if len(data) < max(window, self.atr_window):
            return None
            
        # 计算突破价位
        high_n = data['high'].rolling(window=window).max()
        low_n = data['low'].rolling(window=window).min()
        exit_low = data['low'].rolling(window=exit_window).min()
        exit_high = data['high'].rolling(window=exit_window).max()
        
        # 计算ATR
        atr = self.calculate_atr(data)
        
        # 获取最新数据
        latest_price = data['close'].iloc[-1]
        latest_high_n = high_n.iloc[-1]
        latest_low_n = low_n.iloc[-1]
        latest_exit_low = exit_low.iloc[-1]
        latest_exit_high = exit_high.iloc[-1]
        latest_atr = atr.iloc[-1]
        
        # 计算仓位大小
        position_size = self.calculate_position_size(latest_price, latest_atr)
        
        # 判断突破（放宽突破条件）
        signal = "无"
        if latest_price > latest_high_n * 0.98:  # 允许接近突破位就产生信号
            signal = "买入"
        elif latest_price < latest_exit_low * 1.02:  # 允许接近退出位就产生信号
            signal = "卖出"
            
        # 检查止损条件（放宽止损条件）
        if signal == "无" and len(data) > 1:
            prev_price = data['close'].iloc[-2]
            if self.check_stop_loss(data, prev_price, latest_atr * 1.2):  # 放宽止损条件
                signal = "止损"
                
        return {
            'signal': signal,
            'price': latest_price,
            'atr': latest_atr,
            'position_size': position_size,
            'stop_loss_price': latest_price - (self.stop_loss_atr * latest_atr)
        }
        
    def analyze(self, data):
        """分析数据"""
        try:
            # 验证数据
            if not self._validate_data(data):
                return None
                
            # 分析系统1和系统2
            sys1_result = self.analyze_system(data, self.sys1_window, self.sys1_exit_window)
            sys2_result = self.analyze_system(data, self.sys2_window, self.sys2_exit_window)
            
            if not sys1_result or not sys2_result:
                return None
                
            # 综合两个系统的信号（放宽条件：任一系统产生信号即可）
            final_signal = "无"
            if sys1_result['signal'] == "买入" or sys2_result['signal'] == "买入":
                final_signal = "买入"
            elif sys1_result['signal'] in ["卖出", "止损"] or sys2_result['signal'] in ["卖出", "止损"]:
                final_signal = "卖出"
                
            return {
                'signal': final_signal,
                'sys1': sys1_result,
                'sys2': sys2_result,
                'max_units': self.max_units,
                'current_price': data['close'].iloc[-1]
            }
            
        except Exception as e:
            self.logger.error(f"海龟策略分析失败: {str(e)}")
            return None
            
    def get_signals(self, data):
        """获取买卖信号"""
        try:
            if len(data) < max(self.sys1_window, self.sys2_window, self.atr_window):
                return []
                
            signals = []
            result = self.analyze(data)
            
            if result and result['signal'] != "无":
                signals.append({
                    'date': data.index[-1],
                    'type': result['signal'],
                    'strategy': self.name,
                    'price': result['current_price'],
                    'sys1_signal': result['sys1']['signal'],
                    'sys2_signal': result['sys2']['signal'],
                    'sys1_position': result['sys1']['position_size'],
                    'sys2_position': result['sys2']['position_size'],
                    'stop_loss_price': min(result['sys1']['stop_loss_price'], 
                                         result['sys2']['stop_loss_price'])
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取海龟策略信号失败: {str(e)}")
            return []

__all__ = ['TurtleStrategy']
