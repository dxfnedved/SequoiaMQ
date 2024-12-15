# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class Alpha101Strategy(BaseStrategy):
    """Alpha101 因子策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "Alpha101Strategy"
        self.window_size = 20  # 观察窗口
        self.min_volume = 200000  # 最小成交量（提高到20万）
        self.max_price = 200  # 最高价格限制（降低到200元）
        self.min_price = 5  # 最低价格限制（提高到5元）
        self.alpha1_threshold = 0.02  # Alpha1阈值
        self.alpha2_threshold = 0.015  # Alpha2阈值
        self.alpha3_threshold = -0.03  # Alpha3阈值（反转阈值）
        
    def calculate_alpha1(self, data):
        """计算 Alpha1: 成交量加权的价格动量"""
        try:
            close = data['close']  # Changed from '收盘' to 'close'
            volume = data['volume']  # Changed from '成交量' to 'volume'
            
            # 计算价格变化率
            returns = close.pct_change()
            
            # 计算成交量加权的动量
            alpha1 = (returns * volume).rolling(window=self.window_size).mean()
            
            return alpha1
            
        except Exception as e:
            self.logger.error(f"计算Alpha1失败: {str(e)}")
            return None
            
    def calculate_alpha2(self, data):
        """Alpha2: 价格趋势因子"""
        try:
            close = data['close']  # Changed from '收盘' to 'close'
            high = data['high']  # Changed from '最高' to 'high'
            low = data['low']  # Changed from '最低' to 'low'
            
            # 计算价格和成交量的变化率
            price_range = (high - low) / close
            
            # 计算5日价格趋势
            alpha2 = price_range.rolling(window=5).mean()
            
            return alpha2
            
        except Exception as e:
            self.logger.error(f"计算Alpha2失败: {str(e)}")
            return None
            
    def calculate_alpha3(self, data):
        """Alpha3: 反转因子"""
        try:
            close = data['close']  # Changed from '收盘' to 'close'
            
            # 计算5日收益率
            returns_5d = close.pct_change(periods=5)
            
            # 计算反转因子
            alpha3 = -1 * returns_5d
            
            return alpha3
            
        except Exception as e:
            self.logger.error(f"计算Alpha3失败: {str(e)}")
            return None
            
    def check_basic_conditions(self, data):
        """检查基本条件"""
        try:
            if len(data) < self.window_size:
                return False, "数据不足"
                
            latest = data.iloc[-1]
            
            # 检查价格范围
            if latest['close'] > self.max_price:  # Changed from '收盘' to 'close'
                return False, "价格过高"
            if latest['close'] < self.min_price:  # Changed from '收盘' to 'close'
                return False, "价格过低"
                
            # 检查成交量（改为检查5日平均成交量）
            avg_volume = data['volume'].tail(5).mean()  # Changed from '成交量' to 'volume'
            if avg_volume < self.min_volume:
                return False, "成交量过低"
                
            return True, "通过基本条件检查"
            
        except Exception as e:
            self.logger.error(f"检查基本条件失败: {str(e)}")
            return False, str(e)
            
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.window_size:
                return None
                
            # 检查基本条件
            passed, message = self.check_basic_conditions(data)
            if not passed:
                self.logger.info(f"基本条件检查未通过: {message}")
                return None
                
            # 计算因子
            alpha1 = self.calculate_alpha1(data)
            alpha2 = self.calculate_alpha2(data)
            alpha3 = self.calculate_alpha3(data)
            
            if any(x is None for x in [alpha1, alpha2, alpha3]):
                return None
                
            # 获取最新因子值
            latest_alpha1 = alpha1.iloc[-1]
            latest_alpha2 = alpha2.iloc[-1]
            latest_alpha3 = alpha3.iloc[-1]
            
            # 计算技术指标
            close = data['close']
            ma20 = close.rolling(window=20).mean()
            ma60 = close.rolling(window=60).mean()
            
            # 获取最新价格和均线
            latest_price = close.iloc[-1]
            latest_ma20 = ma20.iloc[-1]
            latest_ma60 = ma60.iloc[-1]
            
            # 综合信号判断
            signal = "无"
            
            # 买入条件：
            # 1. Alpha1大于阈值（动量强）
            # 2. Alpha2低于阈值（波动率适中）
            # 3. Alpha3大于阈值（不是严重超买）
            # 4. 价格在均线之上
            if (latest_alpha1 > self.alpha1_threshold and
                latest_alpha2 < self.alpha2_threshold and
                latest_alpha3 > self.alpha3_threshold and
                latest_price > latest_ma20 > latest_ma60):
                signal = "买入"
            # 卖出条件：
            # 1. Alpha1为负（动量转弱）
            # 2. Alpha2高于阈值（波动加大）
            # 3. 价格跌破均线
            elif (latest_alpha1 < -self.alpha1_threshold and
                  latest_alpha2 > self.alpha2_threshold * 1.5 and
                  latest_price < latest_ma20):
                signal = "卖出"
                
            return {
                'alpha1': latest_alpha1,
                'alpha2': latest_alpha2,
                'alpha3': latest_alpha3,
                'ma20': latest_ma20,
                'ma60': latest_ma60,
                'signal': signal
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
                    'price': data['close'].iloc[-1],  # Changed from '收盘' to 'close'
                    'alpha1': result['alpha1'],
                    'alpha2': result['alpha2'],
                    'alpha3': result['alpha3']
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取Alpha101策略信号失败: {str(e)}")
            return [] 