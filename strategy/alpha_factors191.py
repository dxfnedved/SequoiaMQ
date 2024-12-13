# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class Alpha191Strategy(BaseStrategy):
    """Alpha191 策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "Alpha191Strategy"
        # 设置阈值参数
        self.alpha1_threshold = 0.015  # 趋势强度阈值（降低）
        self.alpha2_threshold = 0.012  # 动量阈值（降低）
        self.alpha3_threshold = 0.015  # 反转阈值（降低）
        self.alpha4_threshold = 0.02  # 波动率阈值（降低）
        self.alpha5_threshold = 0.01  # 趋势确认阈值（降低）
        self.volume_threshold = 1.5  # 成交量放大倍数（降低）
        self.ma_periods = [5, 10, 20, 60]  # 均线周期
        self.rsi_threshold = 45  # RSI阈值（降低）
        
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
            
    def calculate_alpha5(self, data):
        """计算 Alpha5: ��势确认指标"""
        try:
            close = data['收盘']
            
            # 计算多个周期的均线
            mas = {}
            for period in self.ma_periods:
                mas[period] = close.rolling(period).mean()
            
            # 计算均线多头排列得分
            scores = pd.Series(0, index=close.index)
            for i in range(len(self.ma_periods)-1):
                for j in range(i+1, len(self.ma_periods)):
                    p1, p2 = self.ma_periods[i], self.ma_periods[j]
                    scores += (mas[p1] > mas[p2]).astype(int)
                    
            # 归一化得分
            max_scores = len(self.ma_periods) * (len(self.ma_periods) - 1) / 2
            trend_score = scores / max_scores
            return trend_score
            
        except Exception as e:
            self.logger.error(f"计算 Alpha5 失败: {str(e)}")
            return None
            
    def check_volume_surge(self, data):
        """检查成交量放大"""
        try:
            volume = data['成交量']
            volume_ma = volume.rolling(20).mean()
            return volume.iloc[-1] > volume_ma.iloc[-1] * self.volume_threshold
        except Exception as e:
            self.logger.error(f"检查成交量失败: {str(e)}")
            return False
            
    def check_rsi_condition(self, data):
        """检查RSI条件"""
        try:
            close = data['收盘'].values
            rsi = ta.RSI(close, timeperiod=14)
            return rsi[-1] > self.rsi_threshold  # 只要RSI大于阈值即可
        except Exception as e:
            self.logger.error(f"检查RSI失败: {str(e)}")
            return False

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
            alpha5 = self.calculate_alpha5(data)
            
            if any(x is None for x in [alpha1, alpha2, alpha3, alpha4, alpha5]):
                return None
                
            # 获取最新值
            latest_alpha1 = alpha1.iloc[-1]
            latest_alpha2 = alpha2.iloc[-1]
            latest_alpha3 = alpha3.iloc[-1]
            latest_alpha4 = alpha4.iloc[-1]
            latest_alpha5 = alpha5.iloc[-1]
            
            # 检查成交量和RSI条件
            volume_surge = self.check_volume_surge(data)
            rsi_condition = self.check_rsi_condition(data)
            
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
                
            # Alpha5 信号（趋势确认）
            if latest_alpha5 > self.alpha5_threshold:
                buy_signals += 1
            elif latest_alpha5 < -self.alpha5_threshold:
                sell_signals += 1
                
            # 确定最终信号（放宽条件）
            if (buy_signals >= 3 and  # 至少3个因子支持买入（降低）
                (volume_surge or latest_alpha5 > 0)):  # 成交量或趋势任一满足即可
                signal = "买入"
            elif sell_signals >= 3:  # 卖出信号保持相对敏感
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'Alpha1': latest_alpha1,
                'Alpha2': latest_alpha2,
                'Alpha3': latest_alpha3,
                'Alpha4': latest_alpha4,
                'Alpha5': latest_alpha5,
                'volume_surge': volume_surge,
                'rsi_condition': rsi_condition,
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
                    'alpha5': result['Alpha5'],
                    'volume_surge': result['volume_surge'],
                    'rsi_condition': result['rsi_condition'],
                    'buy_signals': result['buy_signals'],
                    'sell_signals': result['sell_signals']
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取Alpha191策略信号失败: {str(e)}")
            return [] 