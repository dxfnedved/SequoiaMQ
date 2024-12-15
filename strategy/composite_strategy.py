# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class CompositeStrategy(BaseStrategy):
    """组合策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "CompositeStrategy"
        self.window_size = 20  # 观察窗口
        self.volume_ratio = 1.5  # 成交量放大倍数
        self.rsi_threshold = 50  # RSI阈值
        
    def calculate_trend(self, data):
        """计算趋势"""
        try:
            close = data['close']  # Changed from '收盘' to 'close'
            
            # 计算均线
            ma5 = close.rolling(window=5).mean()
            ma10 = close.rolling(window=10).mean()
            ma20 = close.rolling(window=20).mean()
            
            # 判断趋势
            trend_up = (ma5 > ma10) & (ma10 > ma20)
            trend_down = (ma5 < ma10) & (ma10 < ma20)
            
            return trend_up, trend_down
            
        except Exception as e:
            self.logger.error(f"计算趋势失败: {str(e)}")
            return None, None
            
    def calculate_support_resistance(self, data):
        """计算支撑阻力位"""
        try:
            close = data['close']  # Changed from '收盘' to 'close'
            
            # 计算布林带
            upper, middle, lower = ta.BBANDS(close.values, timeperiod=20)
            
            # 计算支撑阻力位
            low_list = pd.Series(data['low']).rolling(window=9).min()  # Changed from '最低' to 'low'
            high_list = pd.Series(data['high']).rolling(window=9).max()  # Changed from '最高' to 'high'
            
            # 获取最新值
            support = low_list.iloc[-1]
            resistance = high_list.iloc[-1]
            
            return support, resistance, upper[-1], middle[-1], lower[-1]
            
        except Exception as e:
            self.logger.error(f"计算支撑阻力位失败: {str(e)}")
            return None, None, None, None, None
            
    def calculate_momentum(self, data):
        """计算动量"""
        try:
            close = data['close']  # Changed from '收盘' to 'close'
            high = data['high']  # Changed from '最高' to 'high'
            low = data['low']  # Changed from '最低' to 'low'
            
            # 计算RSI
            rsi = ta.RSI(close.values, timeperiod=14)
            
            # 计算KDJ
            k, d = ta.STOCH(high.values, low.values, close.values)
            j = 3 * k - 2 * d
            
            # 计算MACD
            macd, signal, hist = ta.MACD(close.values)
            
            return rsi[-1], k[-1], d[-1], j[-1], hist[-1]
            
        except Exception as e:
            self.logger.error(f"计算动量失败: {str(e)}")
            return None, None, None, None, None
            
    def calculate_volume_analysis(self, data):
        """计算量价分析"""
        try:
            close = data['close']  # Changed from '收盘' to 'close'
            volume = data['volume']  # Changed from '成交量' to 'volume'
            
            # 计算成交量变化
            volume_ma = volume.rolling(window=20).mean()
            volume_ratio = volume / volume_ma
            
            # 计算量价关系
            price_change = close.pct_change()
            volume_price_corr = price_change.rolling(window=20).corr(volume_ratio)
            
            return volume_ratio.iloc[-1], volume_price_corr.iloc[-1]
            
        except Exception as e:
            self.logger.error(f"计算量价分析失败: {str(e)}")
            return None, None
            
    def calculate_pattern_recognition(self, data):
        """计算形态识别"""
        try:
            open = data['open']  # Added open price
            close = data['close']
            high = data['high']
            low = data['low']
            
            # 计算形态识别指标
            doji = ta.CDLDOJI(open.values, high.values, low.values, close.values)
            hammer = ta.CDLHAMMER(open.values, high.values, low.values, close.values)
            engulfing = ta.CDLENGULFING(open.values, high.values, low.values, close.values)
            
            return doji[-1], hammer[-1], engulfing[-1]
            
        except Exception as e:
            self.logger.error(f"计算形态识别失败: {str(e)}")
            return None, None, None
            
    def calculate_volatility(self, data):
        """计算波动率"""
        try:
            close = data['close']  # Changed from '收盘' to 'close'
            volume = data['volume']  # Changed from '成交量' to 'volume'
            
            # 计算波动率
            returns = close.pct_change()
            volatility = returns.rolling(window=20).std()
            
            # 计算成交量波动率
            volume_change = volume.pct_change()
            volume_volatility = volume_change.rolling(window=20).std()
            
            return volatility.iloc[-1], volume_volatility.iloc[-1]
            
        except Exception as e:
            self.logger.error(f"计算波动率失败: {str(e)}")
            return None, None
            
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.window_size:
                return None
                
            # 计算各项指标
            trend_up, trend_down = self.calculate_trend(data)
            support, resistance, upper, middle, lower = self.calculate_support_resistance(data)
            rsi, k, d, j, macd_hist = self.calculate_momentum(data)
            volume_ratio, volume_price_corr = self.calculate_volume_analysis(data)
            doji, hammer, engulfing = self.calculate_pattern_recognition(data)
            volatility, volume_volatility = self.calculate_volatility(data)
            
            if any(x is None for x in [trend_up, trend_down, support, resistance,
                                     rsi, k, d, j, macd_hist, volume_ratio,
                                     volume_price_corr, doji, hammer, engulfing,
                                     volatility, volume_volatility]):
                return None
                
            # 综合判断
            buy_signals = 0
            sell_signals = 0
            
            # 趋势信号
            if trend_up.iloc[-1]:
                buy_signals += 1
            if trend_down.iloc[-1]:
                sell_signals += 1
                
            # 支撑阻力信号
            if data['close'].iloc[-1] < support:  # Changed from '收盘' to 'close'
                buy_signals += 1
            if data['close'].iloc[-1] > resistance:  # Changed from '收盘' to 'close'
                sell_signals += 1
                
            # 动量信号
            if rsi < self.rsi_threshold and k < 20 and macd_hist > 0:
                buy_signals += 1
            if rsi > 100 - self.rsi_threshold and k > 80 and macd_hist < 0:
                sell_signals += 1
                
            # 量价信号
            if volume_ratio > self.volume_ratio and volume_price_corr > 0:
                buy_signals += 1
            if volume_ratio < 1/self.volume_ratio and volume_price_corr < 0:
                sell_signals += 1
                
            # 形态信号
            if hammer > 0 or engulfing > 0:
                buy_signals += 1
            if doji > 0 and volatility > volatility.mean():
                sell_signals += 1
                
            # 判断最终信号
            if buy_signals >= 3:
                signal = "买入"
            elif sell_signals >= 3:
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'trend_up': trend_up.iloc[-1],
                'trend_down': trend_down.iloc[-1],
                'support': support,
                'resistance': resistance,
                'rsi': rsi,
                'kdj': (k, d, j),
                'macd_hist': macd_hist,
                'volume_ratio': volume_ratio,
                'volume_price_corr': volume_price_corr,
                'patterns': (doji, hammer, engulfing),
                'volatility': volatility,
                'volume_volatility': volume_volatility,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'signal': signal
            }
            
        except Exception as e:
            self.logger.error(f"组合策略分析失败: {str(e)}")
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
                    'price': data['close'].iloc[-1],  # Changed from '收盘' to 'close'
                    'rsi': result['rsi'],
                    'kdj': result['kdj'],
                    'macd_hist': result['macd_hist'],
                    'volume_ratio': result['volume_ratio'],
                    'volume_price_corr': result['volume_price_corr'],
                    'support': result['support'],
                    'resistance': result['resistance'],
                    'buy_signals': result['buy_signals'],
                    'sell_signals': result['sell_signals']
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取组合策略信号失败: {str(e)}")
            return []