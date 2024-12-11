# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class EnterStrategy(BaseStrategy):
    """入场策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "EnterStrategy"
        self.threshold = 30  # 突破观察期
        self.volume_ratio = 1.5  # 放量倍数
        self.price_change = 0.02  # 价格变动阈值
        
    def check_breakthrough(self, data):
        """检查突破"""
        if len(data) < self.threshold + 1:
            return False
            
        # 最后一天收市价
        last_close = data['收盘'].iloc[-1]
        last_open = data['开盘'].iloc[-1]
        
        # 前N天最高价
        data_prev = data.iloc[:-1]
        max_price = data_prev['收盘'].max()
        second_last_close = data_prev['收盘'].iloc[-1]
        
        return (last_close > max_price > second_last_close and 
                max_price > last_open and 
                last_close / last_open > 1.06)
                
    def check_volume(self, data):
        """检查放量"""
        if len(data) < 2:
            return False
            
        # 获取最新的两天数据
        latest_data = data.iloc[-2:]
        
        # 检查价格变动
        price_change = latest_data['收盘'].iloc[-1] / latest_data['收盘'].iloc[0] - 1
        
        # 检查成交量变化
        volume_change = latest_data['成交量'].iloc[-1] / latest_data['成交量'].iloc[0]
        
        return price_change > self.price_change and volume_change > self.volume_ratio
        
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.threshold + 1:
                return None
                
            # 计算各项指标
            breakthrough = self.check_breakthrough(data)
            volume = self.check_volume(data)
            ma5 = ta.MA(data['收盘'].values, timeperiod=5)[-1]
            ma10 = ta.MA(data['收盘'].values, timeperiod=10)[-1]
            ma20 = ta.MA(data['收盘'].values, timeperiod=20)[-1]
            
            # 判断信号
            if breakthrough and volume:
                signal = "买入"
            else:
                signal = "无"
                
            return {
                'breakthrough': breakthrough,
                'volume_signal': volume,
                'ma5': ma5,
                'ma10': ma10,
                'ma20': ma20,
                'signal': signal
            }
            
        except Exception as e:
            print(f"入场策略分析失败: {str(e)}")
            return None
            
    def get_signals(self, data):
        """获取买卖信号"""
        try:
            if len(data) < self.threshold + 1:
                return []
                
            signals = []
            result = self.analyze(data)
            
            if result and result['signal'] == "买入":
                signals.append({
                    'date': data.index[-1],
                    'type': '买入',
                    'strategy': self.name,
                    'price': data['收盘'].iloc[-1],
                    'breakthrough': result['breakthrough'],
                    'volume_signal': result['volume_signal']
                })
                
            return signals
            
        except Exception as e:
            print(f"获取入场策略信号失败: {str(e)}")
            return []
