# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class CompositeStrategy(BaseStrategy):
    """复合策略：集成趋势过滤、入场信号和止损管理"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "CompositeStrategy"
        
        # 交易周期设置
        self.min_holding_days = 7  # 最小持仓天数
        self.max_holding_days = 30  # 最大持仓天数
        
        # MACD参数（趋势过滤）
        self.macd_fast = 8  # 快速EMA周期
        self.macd_slow = 17  # 慢速EMA周期
        self.macd_signal = 9  # 信号周期
        
        # 布林带参数（趋势过滤）
        self.bb_period = 20  # 布林带周期
        self.bb_std = 2  # 标准差倍数
        
        # SKDJ参数（入场信号）
        self.skdj_n = 9  # SKDJ N周期
        self.skdj_m = 3  # SKDJ M周期
        
        # RSI参数（入场信号）
        self.rsi_period = 14  # RSI周期
        self.rsi_upper = 70  # RSI上限
        self.rsi_lower = 30  # RSI下限
        
        # ATR参数（止损设置）
        self.atr_period = 14  # ATR周期
        self.initial_stop_multiplier = 2.0  # 初始止损ATR倍数
        self.trailing_stop_multiplier = 1.5  # 跟踪止损ATR倍数
        
        # 平台突破参数
        self.platform_ma = 60  # 平台突破MA周期
        self.volume_ratio_threshold = 2.0  # 成交量放大倍数
        self.consolidation_days = 3  # 整理天数
        self.price_change_threshold = 0.03  # 价格波动阈值
        self.continuous_up_days = 2  # 连续上涨天数
        self.min_up_ratio = 0.095  # 最小涨幅
        
    def calculate_trend(self, data):
        """计算趋势
        Returns:
            1: 上升趋势
            0: 无明显趋势
            -1: 下降趋势
        """
        try:
            close = data['收盘']
            
            # 计算MACD
            macd, signal, hist = ta.MACD(
                close,
                fastperiod=self.macd_fast,
                slowperiod=self.macd_slow,
                signalperiod=self.macd_signal
            )
            
            # 计算布林带
            upper, middle, lower = ta.BBANDS(
                close,
                timeperiod=self.bb_period,
                nbdevup=self.bb_std,
                nbdevdn=self.bb_std
            )
            
            # 使用iloc访问最后一个元素
            macd_trend = 1 if macd.iloc[-1] > signal.iloc[-1] else (-1 if macd.iloc[-1] < signal.iloc[-1] else 0)
            bb_trend = 1 if close.iloc[-1] > middle.iloc[-1] else (-1 if close.iloc[-1] < middle.iloc[-1] else 0)
            
            # 综合趋势判断
            if macd_trend == bb_trend:
                return macd_trend
            return 0
            
        except Exception as e:
            self.logger.error(f"计算趋势失败: {str(e)}")
            return 0
            
    def calculate_entry_signal(self, data):
        """计算入场信号"""
        try:
            close = data['收盘']
            high = data['最高']
            low = data['最低']
            
            # 计算RSI
            rsi = pd.Series(ta.RSI(close.values, timeperiod=self.rsi_period))
            
            # 计算SKDJ
            low_list = pd.Series(low).rolling(window=self.skdj_n).min()
            high_list = pd.Series(high).rolling(window=self.skdj_n).max()
            rsv = (close - low_list) / (high_list - low_list) * 100
            k = pd.Series(rsv).ewm(alpha=1/self.skdj_m).mean()
            d = pd.Series(k).ewm(alpha=1/self.skdj_m).mean()
            
            # 使用iloc访问最后一个元素
            skdj_signal = 1 if k.iloc[-1] > d.iloc[-1] else (-1 if k.iloc[-1] < d.iloc[-1] else 0)
            rsi_signal = 1 if rsi.iloc[-1] < self.rsi_lower else (-1 if rsi.iloc[-1] > self.rsi_upper else 0)
            
            # 返回信号和指标值
            return {
                'skdj_signal': skdj_signal,
                'rsi_signal': rsi_signal,
                'k': k.iloc[-1],
                'd': d.iloc[-1],
                'rsi': rsi.iloc[-1]
            }
            
        except Exception as e:
            self.logger.error(f"计算入场信号失败: {str(e)}")
            return None
            
    def calculate_stops(self, data, position_type='long'):
        """计算止损价格"""
        try:
            high = data['最高']
            low = data['最低']
            close = data['收盘']
            
            # 计算ATR
            atr = pd.Series(ta.ATR(high, low, close, timeperiod=self.atr_period))
            
            # 使用iloc访问最后一个元素
            latest_close = close.iloc[-1]
            latest_atr = atr.iloc[-1]
            
            if position_type == 'long':
                initial_stop = latest_close - self.initial_stop_multiplier * latest_atr
                trailing_stop = latest_close - self.trailing_stop_multiplier * latest_atr
            else:
                initial_stop = latest_close + self.initial_stop_multiplier * latest_atr
                trailing_stop = latest_close + self.trailing_stop_multiplier * latest_atr
                
            return initial_stop, trailing_stop
            
        except Exception as e:
            self.logger.error(f"计算止损价格失败: {str(e)}")
            return None, None
            
    def check_platform_breakthrough(self, data):
        """检查平台突破形态"""
        try:
            if len(data) < self.platform_ma:
                return False
                
            close = data['收盘']
            open_price = data['开盘']
            volume = data['成交量']
            
            # 计算MA60
            ma60 = pd.Series(ta.MA(close.values, self.platform_ma))
            
            # 计算成交量比率
            volume_ma = volume.rolling(window=20).mean()
            volume_ratio = volume / volume_ma
            
            # 获取最新数据
            latest_data = data.tail(self.consolidation_days + 1)
            
            # 检查MA60突破
            ma_breakthrough = (open_price.iloc[-1] < ma60.iloc[-1] <= close.iloc[-1])
            
            # 检查成交量放大
            volume_amplification = (volume_ratio.iloc[-1] > self.volume_ratio_threshold)
            
            # 检查价格整理
            price_stable = True
            for _, row in latest_data.iterrows():
                if abs(row['收盘'] / row['开盘'] - 1) > self.price_change_threshold:
                    price_stable = False
                    break
            
            return ma_breakthrough and volume_amplification and price_stable
            
        except Exception as e:
            self.logger.error(f"检查平台突破失败: {str(e)}")
            return False
            
    def check_high_tight_flag(self, data):
        """检查高而窄的旗形形态"""
        try:
            if len(data) < 5:  # 至少需要5天数据
                return False
                
            # 检查连续涨停
            continuous_up = 0
            for _, row in data.tail(5).iterrows():
                if row['p_change'] >= self.min_up_ratio * 100:
                    continuous_up += 1
                else:
                    continuous_up = 0
                    
                if continuous_up >= self.continuous_up_days:
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"检查高而窄的旗形失败: {str(e)}")
            return False
            
    def check_parking_apron(self, data):
        """检查停机坪形态"""
        try:
            if len(data) < self.consolidation_days + 1:
                return False
                
            # 获取最近几天数据
            recent_data = data.tail(self.consolidation_days + 1)
            
            # 第一天必须是涨停
            first_day = recent_data.iloc[0]
            if first_day['p_change'] < self.min_up_ratio * 100:
                return False
                
            # 检查后续整理
            consolidation_data = recent_data.iloc[1:]
            for _, row in consolidation_data.iterrows():
                # 价格必须高于涨停价
                if row['收盘'] < first_day['收盘']:
                    return False
                # 日内波动不超过阈值
                if abs(row['收盘'] / row['开盘'] - 1) > self.price_change_threshold:
                    return False
                # 涨跌幅控制在5%以内
                if abs(row['p_change']) > 5:
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"检查停机坪形态失败: {str(e)}")
            return False
            
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < max(self.platform_ma, self.bb_period):
                return None
                
            # 计算趋势
            trend = self.calculate_trend(data)
            
            # 计算入场信号
            entry = self.calculate_entry_signal(data)
            if entry is None:
                return None
                
            # 计算止损价格
            initial_stop, trailing_stop = self.calculate_stops(data, 
                'long' if trend > 0 else 'short')
                
            # 检查各种形态
            platform_signal = self.check_platform_breakthrough(data)
            flag_signal = self.check_high_tight_flag(data)
            parking_signal = self.check_parking_apron(data)
            
            # 综合信号判断
            signal = "无"
            if trend > 0 and entry['skdj_signal'] > 0 and (platform_signal or flag_signal or parking_signal):
                signal = "买入"
            elif trend < 0 or entry['rsi_signal'] < 0:
                signal = "卖出"
                
            return {
                'trend': trend,
                'skdj_k': entry['k'],
                'skdj_d': entry['d'],
                'rsi': entry['rsi'],
                'skdj_signal': entry['skdj_signal'],
                'rsi_signal': entry['rsi_signal'],
                'initial_stop': initial_stop,
                'trailing_stop': trailing_stop,
                'platform_breakthrough': platform_signal,
                'high_tight_flag': flag_signal,
                'parking_apron': parking_signal,
                'signal': signal
            }
            
        except Exception as e:
            self.logger.error(f"复合策略分析失败: {str(e)}")
            return None
            
    def get_signals(self, data):
        """获取买卖信号"""
        try:
            if len(data) < max(self.min_holding_days, self.bb_period):
                return []
                
            signals = []
            result = self.analyze(data)
            
            if result and result['signal'] != "无":
                signals.append({
                    'date': data.index[-1],
                    'type': result['signal'],
                    'strategy': self.name,
                    'price': data['收盘'].iloc[-1],
                    'trend': result['trend'],
                    'skdj_signal': result['skdj_signal'],
                    'rsi_signal': result['rsi_signal'],
                    'skdj_k': result['skdj_k'],
                    'skdj_d': result['skdj_d'],
                    'rsi': result['rsi'],
                    'initial_stop': result['initial_stop'],
                    'trailing_stop': result['trailing_stop'],
                    'platform_breakthrough': result['platform_breakthrough'],
                    'high_tight_flag': result['high_tight_flag'],
                    'parking_apron': result['parking_apron']
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取信号失败: {str(e)}")
            return []