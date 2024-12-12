# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
from strategy.base import BaseStrategy

class Alpha101Strategy(BaseStrategy):
    """Alpha101 策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "Alpha101Strategy"
        # 设置阈值参数
        self.alpha1_threshold = 0.02  # Alpha1 信号阈值
        self.alpha2_threshold = 0.015  # Alpha2 信号阈值
        self.alpha3_threshold = 0.02  # Alpha3 信号阈值
        self.alpha4_threshold = 0.025  # Alpha4 信号阈值
        
    def calculate_alpha1(self, data):
        """计算 Alpha1: 成交量加权的价格动量"""
        try:
            close = data['收盘']
            volume = data['成交量']
            returns = close.pct_change()
            vol_adj_returns = returns * (volume / volume.rolling(10).mean())
            alpha1 = vol_adj_returns.rolling(5).mean()
            return alpha1
        except Exception as e:
            self.logger.error(f"计算 Alpha1 失败: {str(e)}")
            return None

    def calculate_alpha2(self, data):
        """计算 Alpha2: 价格突破强度"""
        try:
            high = data['最高']
            low = data['最低']
            close = data['收盘']
            
            # 计算20日高点和低点
            high_20 = high.rolling(20).max()
            low_20 = low.rolling(20).min()
            
            # 计算突破强度
            breakthrough = (close - low_20) / (high_20 - low_20)
            alpha2 = breakthrough.rolling(5).mean()
            return alpha2
        except Exception as e:
            self.logger.error(f"计算 Alpha2 失败: {str(e)}")
            return None

    def calculate_alpha3(self, data):
        """计算 Alpha3: 量价背离"""
        try:
            close = data['收盘']
            volume = data['成交量']
            
            # 计算价格和成交量的变化率
            price_change = close.pct_change()
            volume_change = volume.pct_change()
            
            # 计算5日价格和成交量趋势
            price_trend = price_change.rolling(5).mean()
            volume_trend = volume_change.rolling(5).mean()
            
            # 量价背离指标
            alpha3 = price_trend - volume_trend
            return alpha3
        except Exception as e:
            self.logger.error(f"计算 Alpha3 失败: {str(e)}")
            return None

    def calculate_alpha4(self, data):
        """计算 Alpha4: 价格动能和波动率"""
        try:
            close = data['收盘']
            high = data['最高']
            low = data['最低']
            
            # 计算波动率
            volatility = ((high - low) / close).rolling(10).std()
            
            # 计算价格动能
            momentum = close.pct_change(5)
            
            # 计算风险调整后的动能
            alpha4 = momentum / volatility
            return alpha4
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
            
            # Alpha1 信号（成交量加权的价格动量）
            if latest_alpha1 > self.alpha1_threshold:
                buy_signals += 1
            elif latest_alpha1 < -self.alpha1_threshold:
                sell_signals += 1
                
            # Alpha2 信号（价格突破强度）
            if latest_alpha2 > self.alpha2_threshold:
                buy_signals += 1
            elif latest_alpha2 < -self.alpha2_threshold:
                sell_signals += 1
                
            # Alpha3 信号（量价背离）
            if latest_alpha3 > self.alpha3_threshold:
                buy_signals += 1
            elif latest_alpha3 < -self.alpha3_threshold:
                sell_signals += 1
                
            # Alpha4 信号（价格动能和波动率）
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
            self.logger.error(f"Alpha101策略分析失败: {str(e)}")
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
            self.logger.error(f"获取Alpha101策略信号失败: {str(e)}")
            return [] 