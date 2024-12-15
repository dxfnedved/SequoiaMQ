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
        self.alpha1_threshold = 0.025  # 趋势强度阈值（提高）
        self.alpha2_threshold = 0.02   # 动量阈值（提高）
        self.alpha3_threshold = 0.025  # 反转阈值（提高）
        self.alpha4_threshold = 0.03   # 波动率阈值（提高）
        self.alpha5_threshold = 0.02   # 趋势确认阈值（提高）
        self.volume_threshold = 2.0    # 成交量放大倍数（提高）
        self.ma_periods = [5, 10, 20, 60]  # 均线周期
        self.rsi_threshold = 55        # RSI阈值（提高）
        self.min_price = 5.0          # 最低价格
        self.max_price = 200.0        # 最高价格
        self.min_volume = 200000      # 最小成交量
        
    def check_basic_conditions(self, data):
        """检查基本条件"""
        try:
            if len(data) < 60:
                return False, "数据不足"
                
            latest = data.iloc[-1]
            
            # 检查价格范围
            if latest['close'] > self.max_price:
                return False, "价格过高"
            if latest['close'] < self.min_price:
                return False, "价格过低"
                
            # 检查成交量
            avg_volume = data['volume'].tail(5).mean()
            if avg_volume < self.min_volume:
                return False, "成交量过低"
                
            # 检查趋势
            ma20 = data['close'].rolling(20).mean()
            ma60 = data['close'].rolling(60).mean()
            if latest['close'] < ma20.iloc[-1] or ma20.iloc[-1] < ma60.iloc[-1]:
                return False, "趋势不符"
                
            return True, "通过基本条件检查"
            
        except Exception as e:
            self.logger.error(f"检查基本条件失败: {str(e)}")
            return False, str(e)
            
    def calculate_alpha1(self, data):
        """计算 Alpha1: 趋势强度指标"""
        try:
            close = data['close']
            high = data['high']
            low = data['low']
            
            # 计算趋势强度
            tr = pd.DataFrame({
                'hl': high - low,
                'hc': abs(high - close.shift(1)),
                'lc': abs(low - close.shift(1))
            }).max(axis=1)
            
            atr = tr.rolling(14).mean()
            trend = (close - close.shift(20)) / (atr * np.sqrt(20))
            
            # 添加趋势确认
            ma20 = close.rolling(20).mean()
            ma60 = close.rolling(60).mean()
            trend_confirm = (ma20 > ma60).astype(int)
            
            return trend * trend_confirm
            
        except Exception as e:
            self.logger.error(f"计算 Alpha1 失败: {str(e)}")
            return None
            
    def calculate_alpha2(self, data):
        """计算 Alpha2: 动量指标"""
        try:
            close = data['close']
            volume = data['volume']
            
            # 计算成交量加权的动量
            returns = close.pct_change()
            volume_ratio = volume / volume.rolling(10).mean()
            momentum = (returns * volume_ratio).rolling(10).sum()
            
            # 添加波动率调整
            volatility = returns.rolling(20).std()
            momentum = momentum / volatility
            
            return momentum
            
        except Exception as e:
            self.logger.error(f"计算 Alpha2 失败: {str(e)}")
            return None

    def calculate_alpha3(self, data):
        """计算 Alpha3: 反转指标"""
        try:
            close = data['close']
            high = data['high']
            low = data['low']
            volume = data['volume']
            
            # 计算超买超卖
            highest_high = high.rolling(10).max()
            lowest_low = low.rolling(10).min()
            
            # 计算价格位置
            price_position = (close - lowest_low) / (highest_high - lowest_low)
            
            # 添加成交量确认
            volume_ratio = volume / volume.rolling(20).mean()
            reversal = (1 - price_position) * volume_ratio
            
            return reversal
            
        except Exception as e:
            self.logger.error(f"计算 Alpha3 失败: {str(e)}")
            return None

    def calculate_alpha4(self, data):
        """计算 Alpha4: 波动率突破指标"""
        try:
            close = data['close']
            
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
        """计算 Alpha5: 趋势确认指标"""
        try:
            close = data['close']
            volume = data['volume']
            
            # 计算均线
            ma5 = close.rolling(5).mean()
            ma10 = close.rolling(10).mean()
            ma20 = close.rolling(20).mean()
            
            # 计算趋势确认信号
            trend_signal = (ma5 > ma10) & (ma10 > ma20)
            volume_signal = volume > volume.rolling(20).mean()
            
            # 综合信号
            alpha5 = pd.Series(0, index=close.index)
            alpha5[trend_signal & volume_signal] = 1
            alpha5[~trend_signal & ~volume_signal] = -1
            
            return alpha5
            
        except Exception as e:
            self.logger.error(f"计算 Alpha5 失败: {str(e)}")
            return None

    def check_volume_surge(self, data):
        """检查成交量放大"""
        try:
            volume = data['volume']
            volume_ma = volume.rolling(20).mean()
            return volume.iloc[-1] > volume_ma.iloc[-1] * self.volume_threshold
            
        except Exception as e:
            self.logger.error(f"检查成交量失败: {str(e)}")
            return False

    def check_rsi_condition(self, data):
        """检查RSI条件"""
        try:
            close = data['close']
            rsi = ta.RSI(close, timeperiod=14)
            return rsi.iloc[-1] > self.rsi_threshold
            
        except Exception as e:
            self.logger.error(f"检查RSI失败: {str(e)}")
            return False

    def _validate_data(self, data):
        """验证数据有效性"""
        try:
            if data is None or len(data) < 60:  # 至少需要60天数据
                return False
                
            required_columns = ['close', 'high', 'low', 'volume']
            if not all(col in data.columns for col in required_columns):
                self.logger.error("数据缺少必要列")
                return False
                
            # 检查数据是否包含无效值
            if data[required_columns].isnull().any().any():
                self.logger.error("数据包含无效值")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"数据验证失败: {str(e)}")
            return False

    def analyze(self, data):
        """分析数据"""
        try:
            # 检查基本条件
            passed, message = self.check_basic_conditions(data)
            if not passed:
                self.logger.info(f"基本条件检查未通过: {message}")
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
            
            # 计算技术指标
            close = data['close']
            ma20 = close.rolling(20).mean()
            ma60 = close.rolling(60).mean()
            
            # 综合信号判断
            buy_signals = 0
            sell_signals = 0
            
            # Alpha1 信号（趋势强度）
            if latest_alpha1 > self.alpha1_threshold and close.iloc[-1] > ma20.iloc[-1]:
                buy_signals += 1
            elif latest_alpha1 < -self.alpha1_threshold and close.iloc[-1] < ma20.iloc[-1]:
                sell_signals += 1
                
            # Alpha2 信号（动量）
            if latest_alpha2 > self.alpha2_threshold and volume_surge:
                buy_signals += 1
            elif latest_alpha2 < -self.alpha2_threshold:
                sell_signals += 1
                
            # Alpha3 信号（反转）
            if latest_alpha3 > self.alpha3_threshold and rsi_condition:
                buy_signals += 1
            elif latest_alpha3 < -self.alpha3_threshold:
                sell_signals += 1
                
            # Alpha4 信号（波动率）
            if latest_alpha4 < self.alpha4_threshold and volume_surge:  # 低波动优先
                buy_signals += 1
            elif latest_alpha4 > self.alpha4_threshold * 1.5:
                sell_signals += 1
                
            # Alpha5 信号（趋势确认）
            if latest_alpha5 > self.alpha5_threshold and ma20.iloc[-1] > ma60.iloc[-1]:
                buy_signals += 1
            elif latest_alpha5 < -self.alpha5_threshold and ma20.iloc[-1] < ma60.iloc[-1]:
                sell_signals += 1
                
            # 确定最终信号（提高条件）
            if (buy_signals >= 4 and  # 至少4个因子支持买入（提高）
                volume_surge and      # 必须有成交量配合
                rsi_condition and     # 必须满足RSI条件
                close.iloc[-1] > ma20.iloc[-1] > ma60.iloc[-1]):  # 必须满足趋势条件
                signal = "买入"
            elif (sell_signals >= 3 and  # 卖出信号保持相对敏感
                  (close.iloc[-1] < ma20.iloc[-1] or latest_alpha4 > self.alpha4_threshold * 1.5)):
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
                'ma20': ma20.iloc[-1],
                'ma60': ma60.iloc[-1],
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
                    'price': data['close'].iloc[-1],
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