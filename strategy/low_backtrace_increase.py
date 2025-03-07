# -*- encoding: UTF-8 -*-
import logging
import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class LowBacktraceIncreaseStrategy(BaseStrategy):
    """低回撤稳步上涨策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "LowBacktraceIncreaseStrategy"
        self.description = "低回撤稳步上涨策略 - 寻找稳定增长且回撤较小的股票"
        self.version = "2.0.0"
        
        # 策略参数
        self.window_size = 20  # 观察窗口
        self.ma_window = 20  # 均线周期
        self.min_increase = 0.1  # 最小涨幅
        self.max_backtrace = 0.05  # 最大回撤
        self.min_data_length = self.window_size + 10  # 最小数据长度
        
    def _analyze_impl(self, data):
        """实现低回撤上涨策略分析"""
        try:
            # 获取最近window_size天的数据
            recent_data = data.tail(self.window_size)
            
            # 计算涨幅和回撤
            increase, max_backtrace = self._calculate_increase(recent_data)
            
            if increase is None or max_backtrace is None:
                return None
                
            # 计算均线
            ma = data['close'].rolling(window=self.ma_window).mean()
            
            # 获取最新数据
            latest_close = data['close'].iloc[-1]
            latest_ma = ma.iloc[-1]
            
            # 计算买入卖出强度
            buy_strength = max(0, min(1, (increase - self.min_increase) / self.min_increase))
            sell_strength = max(0, min(1, (max_backtrace - self.max_backtrace) / self.max_backtrace))
            
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
                'signal': signal,
                'buy_strength': buy_strength,
                'sell_strength': sell_strength,
                'factors': {
                    'increase': increase,
                    'max_backtrace': max_backtrace,
                    'price_to_ma': latest_close / latest_ma - 1
                }
            }
            
        except Exception as e:
            self.logger.error(f"低回撤上涨策略分析失败: {str(e)}")
            return None
            
    def _calculate_increase(self, data):
        """计算涨幅和最大回撤"""
        try:
            # 使用缓存键
            cache_key = (data.index[-1].strftime('%Y%m%d'), len(data))
            
            # 尝试从缓存获取
            cached_result = self._calculate_indicator('increase_backtrace', cache_key)
            if cached_result is not None:
                return cached_result
                
            close = data['close']
            
            # 计算历史最高价
            high_price = close.expanding().max()
            
            # 计算回撤
            backtrace = (high_price - close) / high_price
            
            # 计算总涨幅
            total_increase = close.iloc[-1] / close.iloc[0] - 1
            
            result = (total_increase, backtrace.max())
            
            # 更新缓存
            self._indicator_cache[(
                'increase_backtrace', 
                cache_key, 
                frozenset()
            )] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"计算涨幅失败: {str(e)}")
            return None, None
            
    def _extract_signals(self, data, result):
        """从分析结果中提取信号"""
        signals = []
        
        if result and result['signal'] != "无":
            signals.append({
                'date': data.index[-1],
                'type': result['signal'],
                'strategy': self.name,
                'price': data['close'].iloc[-1],
                'increase': result['increase'],
                'max_backtrace': result['max_backtrace'],
                'ma': result['ma'],
                'strength': result['buy_strength'] if result['signal'] == "买入" else result['sell_strength'],
                'factors': result.get('factors', {})
            })
                
        return signals
