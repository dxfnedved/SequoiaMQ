import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class Alpha360Strategy(BaseStrategy):
    """Alpha360策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "Alpha360Strategy"
        # 设置阈值参数
        self.momentum_threshold = 0.03  # 动量阈值
        self.volume_threshold = 2.0  # 成交量阈值
        self.volatility_threshold = 0.02  # 波动率阈值
        self.trend_threshold = 0.01  # 趋势阈值
        self.window_size = 20  # 基础观察窗口
        
    def calculate_momentum_factors(self, data):
        """计算动量类因子"""
        close = data['close']
        volume = data['volume']
        
        factors = {}
        # 价格动量
        factors['mom_1m'] = close.pct_change(20)
        factors['mom_3m'] = close.pct_change(60)
        factors['mom_6m'] = close.pct_change(120)
        
        # 成交量加权动量
        vwap = (close * volume).rolling(20).sum() / volume.rolling(20).sum()
        factors['vwap_mom'] = (close - vwap) / vwap
        
        # RSI
        factors['rsi'] = pd.Series(ta.RSI(close.values, timeperiod=14))
        
        return pd.DataFrame(factors)
        
    def calculate_volume_factors(self, data):
        """计算成交量类因子"""
        volume = data['volume']
        close = data['close']
        
        factors = {}
        # 成交量变化
        factors['vol_change'] = volume.pct_change()
        factors['vol_ma_ratio'] = volume / volume.rolling(20).mean()
        
        # 量价关系
        factors['vol_price_corr'] = close.rolling(20).corr(volume)
        factors['vol_price_disp'] = (close.pct_change() * volume.pct_change()).rolling(20).mean()
        
        return pd.DataFrame(factors)
        
    def calculate_volatility_factors(self, data):
        """计算波动率类因子"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        factors = {}
        # ATR
        factors['atr'] = pd.Series(ta.ATR(high.values, low.values, close.values))
        
        # 波动率
        factors['volatility'] = close.rolling(20).std() / close.rolling(20).mean()
        
        # 价格区间
        factors['price_range'] = (high - low) / close
        
        return pd.DataFrame(factors)
        
    def calculate_trend_factors(self, data):
        """计算趋势类因子"""
        close = data['close']
        
        factors = {}
        # 均线系统
        for period in [5, 10, 20, 60]:
            ma = close.rolling(period).mean()
            factors[f'ma{period}_slope'] = (ma - ma.shift(1)) / ma.shift(1)
            factors[f'ma{period}_pos'] = (close - ma) / ma
            
        # MACD
        macd, signal, hist = ta.MACD(close.values)
        factors['macd'] = pd.Series(macd)
        factors['macd_signal'] = pd.Series(signal)
        factors['macd_hist'] = pd.Series(hist)
        
        return pd.DataFrame(factors)
        
    def analyze(self, data):
        """分析数据"""
        try:
            if not self._validate_data(data):
                return None
                
            # 计算各类因子
            momentum_factors = self.calculate_momentum_factors(data)
            volume_factors = self.calculate_volume_factors(data)
            volatility_factors = self.calculate_volatility_factors(data)
            trend_factors = self.calculate_trend_factors(data)
            
            # 获取最新值
            latest = {
                'momentum': momentum_factors.iloc[-1],
                'volume': volume_factors.iloc[-1],
                'volatility': volatility_factors.iloc[-1],
                'trend': trend_factors.iloc[-1]
            }
            
            # 信号判断
            buy_signals = 0
            sell_signals = 0
            
            # 动量信号
            if latest['momentum']['mom_1m'] > self.momentum_threshold:
                buy_signals += 1
            elif latest['momentum']['mom_1m'] < -self.momentum_threshold:
                sell_signals += 1
                
            if latest['momentum']['rsi'] < 30:
                buy_signals += 1
            elif latest['momentum']['rsi'] > 70:
                sell_signals += 1
                
            # 成交量信号
            if latest['volume']['vol_ma_ratio'] > self.volume_threshold:
                if latest['volume']['vol_price_corr'] > 0:
                    buy_signals += 1
                else:
                    sell_signals += 1
                    
            # 波动率信号
            if latest['volatility']['volatility'] < self.volatility_threshold:
                buy_signals += 1
            elif latest['volatility']['volatility'] > self.volatility_threshold * 2:
                sell_signals += 1
                
            # 趋势信号
            for period in [5, 10, 20, 60]:
                if latest['trend'][f'ma{period}_pos'] > self.trend_threshold:
                    buy_signals += 1
                elif latest['trend'][f'ma{period}_pos'] < -self.trend_threshold:
                    sell_signals += 1
                    
            # 确定最终信号（至少需要3个子信号支持）
            if buy_signals >= 3:
                signal = "买入"
            elif sell_signals >= 3:
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'signal': signal,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'momentum_factors': dict(latest['momentum']),
                'volume_factors': dict(latest['volume']),
                'volatility_factors': dict(latest['volatility']),
                'trend_factors': dict(latest['trend'])
            }
            
        except Exception as e:
            self.logger.error(f"Alpha360策略分析失败: {str(e)}")
            return None
            
    def get_signals(self, data):
        """获取买卖信号"""
        try:
            if not self._validate_data(data):
                return []
                
            signals = []
            result = self.analyze(data)
            
            if result and result['signal'] != "无":
                signals.append({
                    'date': data.index[-1],
                    'type': result['signal'],
                    'strategy': self.name,
                    'price': data['close'].iloc[-1],
                    'buy_signals': result['buy_signals'],
                    'sell_signals': result['sell_signals'],
                    'factors': {
                        'momentum': result['momentum_factors'],
                        'volume': result['volume_factors'],
                        'volatility': result['volatility_factors'],
                        'trend': result['trend_factors']
                    }
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取Alpha360策略信号失败: {str(e)}")
            return [] 