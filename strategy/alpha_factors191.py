# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
from strategy.base import BaseStrategy

class Alpha191Strategy(BaseStrategy):
    """Alpha191 策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "Alpha191Strategy"
        # 设置阈值参数
        self.alpha1_threshold = 0.02  # 趋势强度阈值
        self.alpha2_threshold = 0.015  # 动量阈值
        self.alpha3_threshold = 0.02  # 反转阈值
        self.alpha4_threshold = 0.025  # 波动率阈值
        
    def calculate_alpha1(self, data):
        """计算 Alpha1: 趋势强度指标"""
        try:
            close = data['收盘']
            high = data['最高']
            low = data['最低']
            
            # 计算趋势强度
            tr = pd.DataFrame({
                'hl': high - low,
                'hc': abs(high - close.shift(1)),
                'lc': abs(low - close.shift(1))
            }).max(axis=1)
            
            atr = tr.rolling(14).mean()
            trend = (close - close.shift(20)) / (atr * np.sqrt(20))
            return trend
            
        except Exception as e:
            self.logger.error(f"计算 Alpha1 失败: {str(e)}")
            return None

    def calculate_alpha2(self, data):
        """计算 Alpha2: 动量指标"""
        try:
            close = data['收盘']
            volume = data['成交量']
            
            # 计算成交量加权的动量
            returns = close.pct_change()
            volume_ratio = volume / volume.rolling(10).mean()
            momentum = (returns * volume_ratio).rolling(10).sum()
            return momentum
            
        except Exception as e:
            self.logger.error(f"计算 Alpha2 失败: {str(e)}")
            return None

    def calculate_alpha3(self, data):
        """计算 Alpha3: 反转指标"""
        try:
            close = data['收盘']
            high = data['最高']
            low = data['最低']
            
            # 计算超买超卖
            highest_high = high.rolling(10).max()
            lowest_low = low.rolling(10).min()
            
            # 计算价格位置
            price_position = (close - lowest_low) / (highest_high - lowest_low)
            reversal = 1 - price_position  # 反转信号
            return reversal
            
        except Exception as e:
            self.logger.error(f"计算 Alpha3 失败: {str(e)}")
            return None

    def calculate_alpha4(self, data):
        """计算 Alpha4: 波动率突破指标"""
        try:
            close = data['收盘']
            
            # 计算波动率
            returns = close.pct_change()
            volatility = returns.rolling(20).std()
            
            # 计算波动率变化
            vol_ratio = volatility / volatility.rolling(60).mean()
            return vol_ratio
            
        except Exception as e:
            self.logger.error(f"计算 Alpha4 失败: {str(e)}")
            return None

    def analyze(self, data):
        """分析数据"""
        try:
            if not self._validate_data(data):
                return None
                
            # 计算各个Alpha因子
            alpha1 = self.calculate_alpha1(data)
            alpha2 = self.calculate_alpha2(data)
            alpha3 = self.calculate_alpha3(data)
            alpha4 = self.calculate_alpha4(data)
            
            if any(x is None for x in [alpha1, alpha2, alpha3, alpha4]):
                return None
                
            # 获取最新值
            latest_alpha1 = alpha1.iloc[-1]
            latest_alpha2 = alpha2.iloc[-1]
            latest_alpha3 = alpha3.iloc[-1]
            latest_alpha4 = alpha4.iloc[-1]
            
            # 综合信号判断
            buy_signals = 0
            sell_signals = 0
            
            # Alpha1 信号（趋势强度）
            if latest_alpha1 > self.alpha1_threshold:
                buy_signals += 1
            elif latest_alpha1 < -self.alpha1_threshold:
                sell_signals += 1
                
            # Alpha2 信号（动量）
            if latest_alpha2 > self.alpha2_threshold:
                buy_signals += 1
            elif latest_alpha2 < -self.alpha2_threshold:
                sell_signals += 1
                
            # Alpha3 信号（反转）
            if latest_alpha3 > self.alpha3_threshold:
                buy_signals += 1
            elif latest_alpha3 < -self.alpha3_threshold:
                sell_signals += 1
                
            # Alpha4 信号（波动率）
            if latest_alpha4 > self.alpha4_threshold:
                buy_signals += 1
            elif latest_alpha4 < -self.alpha4_threshold:
                sell_signals += 1
                
            # 确定最终信号
            if buy_signals >= 3:  # 至少3个因子支持买入
                signal = "买入"
            elif sell_signals >= 3:  # 至少3个因子支持卖出
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'Alpha1': latest_alpha1,
                'Alpha2': latest_alpha2,
                'Alpha3': latest_alpha3,
                'Alpha4': latest_alpha4,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'signal': signal
            }
            
        except Exception as e:
            self.logger.error(f"Alpha191策略分析失败: {str(e)}")
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
                    'price': data['收盘'].iloc[-1],
                    'alpha1': result['Alpha1'],
                    'alpha2': result['Alpha2'],
                    'alpha3': result['Alpha3'],
                    'alpha4': result['Alpha4'],
                    'buy_signals': result['buy_signals'],
                    'sell_signals': result['sell_signals']
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取Alpha191策略信号失败: {str(e)}")
            return [] 