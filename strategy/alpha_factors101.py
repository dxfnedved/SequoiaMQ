# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
import talib as ta
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import akshare as ak
from strategy.base import BaseStrategy
from logger_manager import LoggerManager
import traceback

class Alpha101Strategy(BaseStrategy):
    """Alpha101策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "Alpha101Strategy"
        self.window_size = 250  # 回溯窗口大小
        
        # 设置参数
        self.beta_halflife = 60  # Beta因子半衰期
        self.momentum_halflife = 120  # 动量因子半衰期
        self.vol_halflife = 40  # 波动率因子半衰期
        
    def calculate_exponential_weights(self, window, halflife):
        """计算指数衰减权重"""
        weights = np.exp(-np.log(2) / halflife * np.arange(window))
        return weights / weights.sum()
        
    def calculate_momentum_factors(self, data):
        """计算动量类因子"""
        try:
            returns = data['收盘'].pct_change()
            
            # 计算各种时间窗口的动量
            momentum_12m = returns.rolling(window=250).sum()  # 12个月动量
            momentum_6m = returns.rolling(window=120).sum()   # 6个月动量
            momentum_3m = returns.rolling(window=60).sum()    # 3个月动量
            
            # 计算加权动量
            weights = self.calculate_exponential_weights(120, self.momentum_halflife)
            weighted_momentum = (returns.iloc[-120:] * weights).sum()
            
            return {
                'momentum_12m': momentum_12m.iloc[-1],
                'momentum_6m': momentum_6m.iloc[-1],
                'momentum_3m': momentum_3m.iloc[-1],
                'weighted_momentum': weighted_momentum
            }
        except Exception as e:
            self.logger.error(f"计算动量因子失败: {str(e)}")
            return {'momentum_12m': 0, 'momentum_6m': 0, 'momentum_3m': 0, 'weighted_momentum': 0}
            
    def calculate_reversal_factors(self, data):
        """计算反转类因子"""
        try:
            returns = data['收盘'].pct_change()
            
            # 短期反转
            st_reversal = -1 * returns.rolling(window=5).sum()
            
            # 中期反转
            mt_reversal = -1 * returns.rolling(window=20).sum()
            
            # 长期反转
            lt_reversal = -1 * returns.rolling(window=60).sum()
            
            return {
                'st_reversal': st_reversal.iloc[-1],
                'mt_reversal': mt_reversal.iloc[-1],
                'lt_reversal': lt_reversal.iloc[-1]
            }
        except Exception as e:
            self.logger.error(f"计算反转因子失败: {str(e)}")
            return {'st_reversal': 0, 'mt_reversal': 0, 'lt_reversal': 0}
            
    def calculate_volatility_factors(self, data):
        """计算波动率类因子"""
        try:
            returns = data['收盘'].pct_change()
            
            # 计算不同时间窗口的波动率
            vol_250d = returns.rolling(window=250).std()
            vol_120d = returns.rolling(window=120).std()
            vol_60d = returns.rolling(window=60).std()
            
            # 计算衰减波动率
            weights = self.calculate_exponential_weights(250, self.vol_halflife)
            weighted_vol = np.sqrt((returns.iloc[-250:] ** 2 * weights).sum())
            
            return {
                'vol_250d': vol_250d.iloc[-1],
                'vol_120d': vol_120d.iloc[-1],
                'vol_60d': vol_60d.iloc[-1],
                'weighted_vol': weighted_vol
            }
        except Exception as e:
            self.logger.error(f"计算波动率因子失败: {str(e)}")
            return {'vol_250d': 0, 'vol_120d': 0, 'vol_60d': 0, 'weighted_vol': 0}
            
    def calculate_volume_factors(self, data):
        """计算成交量类因子"""
        try:
            volume = data['成交量']
            close = data['收盘']
            
            # 计算成交量动量
            vol_momentum = volume.pct_change().rolling(window=20).sum()
            
            # 计算成交量波动率
            vol_volatility = volume.pct_change().rolling(window=20).std()
            
            # 计算成交量加权价格
            vwap = (close * volume).rolling(window=20).sum() / volume.rolling(window=20).sum()
            
            # 计算相对成交量
            avg_volume = volume.rolling(window=20).mean()
            relative_volume = volume / avg_volume
            
            return {
                'vol_momentum': vol_momentum.iloc[-1],
                'vol_volatility': vol_volatility.iloc[-1],
                'vwap_ratio': (close.iloc[-1] / vwap.iloc[-1]) - 1,
                'relative_volume': relative_volume.iloc[-1]
            }
        except Exception as e:
            self.logger.error(f"计算成交量因子失败: {str(e)}")
            return {'vol_momentum': 0, 'vol_volatility': 0, 'vwap_ratio': 0, 'relative_volume': 0}
            
    def calculate_correlation_factors(self, data):
        """计算相关性类因子"""
        try:
            returns = data['收盘'].pct_change()
            volume = data['成交量']
            high = data['最高']
            low = data['最低']
            
            # 收益率和成交量的相关性
            ret_vol_corr = returns.rolling(window=60).corr(volume.pct_change())
            
            # 高低价差和成交量的相关性
            hl_range = (high - low) / low
            range_vol_corr = hl_range.rolling(window=60).corr(volume)
            
            return {
                'ret_vol_corr': ret_vol_corr.iloc[-1],
                'range_vol_corr': range_vol_corr.iloc[-1]
            }
        except Exception as e:
            self.logger.error(f"计算相关性因子失败: {str(e)}")
            return {'ret_vol_corr': 0, 'range_vol_corr': 0}
            
    def calculate_technical_factors(self, data):
        """计算技术指标类因子"""
        try:
            close = data['收盘']
            high = data['最高']
            low = data['最低']
            
            # RSI
            rsi = ta.RSI(close.values, timeperiod=14)
            
            # MACD
            macd, signal, hist = ta.MACD(close.values)
            
            # Bollinger Bands
            upper, middle, lower = ta.BBANDS(close.values)
            bb_width = (upper - lower) / middle
            
            # ATR
            atr = ta.ATR(high.values, low.values, close.values)
            
            return {
                'rsi': rsi[-1],
                'macd': macd[-1],
                'bb_width': bb_width[-1],
                'atr': atr[-1]
            }
        except Exception as e:
            self.logger.error(f"计算技术指标因子失败: {str(e)}")
            return {'rsi': 0, 'macd': 0, 'bb_width': 0, 'atr': 0}
            
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.window_size:
                return None
                
            # 计算各类因子
            momentum = self.calculate_momentum_factors(data)
            reversal = self.calculate_reversal_factors(data)
            volatility = self.calculate_volatility_factors(data)
            volume = self.calculate_volume_factors(data)
            correlation = self.calculate_correlation_factors(data)
            technical = self.calculate_technical_factors(data)
            
            # 构建因子矩阵
            factor_values = {
                # 动量因子
                'momentum_12m': momentum['momentum_12m'],
                'momentum_6m': momentum['momentum_6m'],
                'momentum_3m': momentum['momentum_3m'],
                'weighted_momentum': momentum['weighted_momentum'],
                
                # 反转因子
                'st_reversal': reversal['st_reversal'],
                'mt_reversal': reversal['mt_reversal'],
                'lt_reversal': reversal['lt_reversal'],
                
                # 波动率因子
                'vol_250d': volatility['vol_250d'],
                'vol_120d': volatility['vol_120d'],
                'vol_60d': volatility['vol_60d'],
                'weighted_vol': volatility['weighted_vol'],
                
                # 成交量因子
                'vol_momentum': volume['vol_momentum'],
                'vol_volatility': volume['vol_volatility'],
                'vwap_ratio': volume['vwap_ratio'],
                'relative_volume': volume['relative_volume'],
                
                # 相关性因子
                'ret_vol_corr': correlation['ret_vol_corr'],
                'range_vol_corr': correlation['range_vol_corr'],
                
                # 技术指标因子
                'rsi': technical['rsi'],
                'macd': technical['macd'],
                'bb_width': technical['bb_width'],
                'atr': technical['atr']
            }
            
            # 因子标准化
            factor_df = pd.DataFrame([factor_values])
            normalized_factors = StandardScaler().fit_transform(factor_df)
            
            # 计算综合得分
            weights = np.ones(len(factor_values)) / len(factor_values)  # 等权重
            score = np.dot(normalized_factors[0], weights)
            
            # 生成信号
            current_price = data['收盘'].iloc[-1]
            prev_price = data['收盘'].iloc[-2]
            
            if score > 0.1 and current_price > prev_price:  # 阈值可调整
                signal = "买入"
            elif score < -0.1 and current_price < prev_price:
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'signal': signal,
                'score': score,
                'factors': factor_values
            }
            
        except Exception as e:
            self.logger.error(f"Alpha101策略分析失败: {str(e)}")
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
                    'score': result['score'],
                    'factors': result['factors']
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取Alpha101策略信号失败: {str(e)}")
            return [] 