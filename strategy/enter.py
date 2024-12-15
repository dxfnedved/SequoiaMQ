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
        self.window_size = 20  # 观察窗口
        self.volume_ratio = 1.5  # 成交量放大倍数
        self.price_change_threshold = 0.03  # 价格变化阈值
        
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.window_size + 1:
                return None
                
            # 获取最新价格
            last_close = data['close'].iloc[-1]  # Changed from '收盘' to 'close'
            last_open = data['open'].iloc[-1]  # Changed from '开盘' to 'open'
            
            # 前N天最高价
            data_prev = data.iloc[:-1]
            max_price = data_prev['close'].max()  # Changed from '收盘' to 'close'
            second_last_close = data_prev['close'].iloc[-1]  # Changed from '收盘' to 'close'
            
            # 计算均线
            ma5 = data['close'].rolling(window=5).mean()  # Changed from '收盘' to 'close'
            ma10 = data['close'].rolling(window=10).mean()  # Changed from '收盘' to 'close'
            ma20 = data['close'].rolling(window=20).mean()  # Changed from '收盘' to 'close'
            
            # 获取最近N天数据
            latest_data = data.tail(self.window_size)
            
            # 计算价格变化
            price_change = latest_data['close'].iloc[-1] / latest_data['close'].iloc[0] - 1  # Changed from '收盘' to 'close'
            
            # 检查成交量变化
            volume_change = latest_data['volume'].iloc[-1] / latest_data['volume'].iloc[0]  # Changed from '成交量' to 'volume'
            
            # 计算技术指标
            ma5 = ta.MA(data['close'].values, timeperiod=5)[-1]  # Changed from '收盘' to 'close'
            ma10 = ta.MA(data['close'].values, timeperiod=10)[-1]  # Changed from '收盘' to 'close'
            ma20 = ta.MA(data['close'].values, timeperiod=20)[-1]  # Changed from '收盘' to 'close'
            
            # 判断信号
            if (last_close > second_last_close and  # 收盘价上涨
                last_close > last_open and  # 收盘价高于开盘价
                volume_change > self.volume_ratio and  # 成交量放大
                price_change > self.price_change_threshold and  # 价格上涨超过阈值
                last_close > ma5 > ma10 > ma20):  # 均线多头排列
                signal = "买入"
            elif (last_close < second_last_close and  # 收盘价下跌
                  last_close < last_open and  # 收盘价低于开盘价
                  last_close < ma20):  # 跌破20日均线
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'price_change': price_change,
                'volume_change': volume_change,
                'ma5': ma5,
                'ma10': ma10,
                'ma20': ma20,
                'signal': signal
            }
            
        except Exception as e:
            self.logger.error(f"入场策略分析失败: {str(e)}")
            return None
            
    def get_signals(self, data):
        """获取买卖信号"""
        try:
            if len(data) < self.window_size + 1:
                return []
                
            signals = []
            result = self.analyze(data)
            
            if result and result['signal'] != "无":
                signals.append({
                    'date': data.index[-1],
                    'type': result['signal'],
                    'strategy': self.name,
                    'price': data['close'].iloc[-1],  # Changed from '收盘' to 'close'
                    'price_change': result['price_change'],
                    'volume_change': result['volume_change'],
                    'ma5': result['ma5'],
                    'ma10': result['ma10'],
                    'ma20': result['ma20']
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取入场策略信号失败: {str(e)}")
            return []
