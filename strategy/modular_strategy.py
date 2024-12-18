# -*- encoding: UTF-8 -*-

import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class ModularStrategy(BaseStrategy):
    """
    Modular quantitative trading strategy optimized for 5-22 day trading period.
    Combines trend filtering, entry triggers, stop-loss mechanisms, and risk management.
    """
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "ModularStrategy"
        
        # Trend Filter Parameters
        self.macd_fast = 8      # Faster EMA for shorter timeframe
        self.macd_slow = 17     # Slower EMA optimized for 5-22 day period
        self.macd_signal = 9    # Signal line period
        self.bb_period = 15     # Bollinger Bands period optimized for timeframe
        self.bb_std = 2.0       # Standard deviation for Bollinger Bands
        
        # Entry Trigger Parameters
        self.alpha_threshold = 0.02  # Alpha factor threshold
        self.rsi_period = 10        # RSI period optimized for shorter timeframe
        self.rsi_oversold = 30      # RSI oversold level
        self.rsi_overbought = 70    # RSI overbought level
        self.skdj_period = 12       # SKDJ period
        self.skdj_smooth = 3        # SKDJ smoothing factor
        
        # Stop-Loss Parameters
        self.atr_period = 10        # ATR period for stop-loss
        self.initial_stop_atr = 2.0 # Initial stop-loss ATR multiplier
        self.trailing_stop_atr = 1.5 # Trailing stop-loss ATR multiplier
        self.fixed_stop_pct = 0.02  # Fixed percentage stop-loss (2%)
        
        # Volume and Volatility Filters
        self.volume_ma_period = 10  # Volume moving average period
        self.volume_threshold = 1.5  # Volume surge threshold
        self.volatility_period = 10  # Volatility calculation period
        self.max_volatility = 0.03  # Maximum allowed volatility
        
    def calculate_trend_indicators(self, data):
        """Calculate trend indicators (MACD and Bollinger Bands)"""
        try:
            close = data['close']
            
            # Calculate MACD
            macd, signal, hist = ta.MACD(
                close,
                fastperiod=self.macd_fast,
                slowperiod=self.macd_slow,
                signalperiod=self.macd_signal
            )
            
            # Calculate Bollinger Bands
            bb_upper, bb_middle, bb_lower = ta.BBANDS(
                close,
                timeperiod=self.bb_period,
                nbdevup=self.bb_std,
                nbdevdn=self.bb_std
            )
            
            # Calculate trend strength
            trend_strength = (close - bb_middle) / (bb_upper - bb_lower)
            
            return {
                'macd': macd,
                'macd_signal': signal,
                'macd_hist': hist,
                'bb_upper': bb_upper,
                'bb_middle': bb_middle,
                'bb_lower': bb_lower,
                'trend_strength': trend_strength
            }
            
        except Exception as e:
            self.logger.error(f"计算趋势指标失败: {str(e)}")
            return None
            
    def calculate_entry_triggers(self, data):
        """Calculate entry trigger indicators (Alpha, RSI, SKDJ)"""
        try:
            close = data['close']
            high = data['high']
            low = data['low']
            volume = data['volume']
            
            # Calculate RSI
            rsi = ta.RSI(close, timeperiod=self.rsi_period)
            
            # Calculate SKDJ (Slow KDJ)
            k, d = ta.STOCH(
                high, low, close,
                fastk_period=self.skdj_period,
                slowk_period=self.skdj_smooth,
                slowd_period=self.skdj_smooth
            )
            
            # Calculate Alpha factor (price momentum with volume)
            returns = close.pct_change()
            volume_ratio = volume / volume.rolling(self.volume_ma_period).mean()
            alpha = (returns * volume_ratio).rolling(window=10).mean()
            
            return {
                'rsi': rsi,
                'stoch_k': k,
                'stoch_d': d,
                'alpha': alpha
            }
            
        except Exception as e:
            self.logger.error(f"计算入场触发指标失败: {str(e)}")
            return None
            
    def calculate_stop_levels(self, data):
        """Calculate initial and trailing stop-loss levels"""
        try:
            close = data['close']
            high = data['high']
            low = data['low']
            
            # Calculate ATR
            atr = ta.ATR(high, low, close, timeperiod=self.atr_period)
            
            # Calculate stop levels
            initial_stop = close - (atr * self.initial_stop_atr)
            trailing_stop = close - (atr * self.trailing_stop_atr)
            fixed_stop = close * (1 - self.fixed_stop_pct)
            
            # Use the highest (most conservative) stop level
            final_stop = pd.concat([initial_stop, trailing_stop, fixed_stop], axis=1).max(axis=1)
            
            return {
                'atr': atr,
                'initial_stop': initial_stop,
                'trailing_stop': trailing_stop,
                'fixed_stop': fixed_stop,
                'final_stop': final_stop
            }
            
        except Exception as e:
            self.logger.error(f"计算止损位失败: {str(e)}")
            return None
            
    def check_volume_volatility(self, data):
        """Check volume and volatility conditions"""
        try:
            close = data['close']
            volume = data['volume']
            
            # Calculate volume ratio
            volume_ma = volume.rolling(window=self.volume_ma_period).mean()
            volume_ratio = volume / volume_ma
            
            # Calculate volatility
            returns = close.pct_change()
            volatility = returns.rolling(window=self.volatility_period).std()
            
            return {
                'volume_ratio': volume_ratio,
                'volatility': volatility,
                'volume_valid': volume_ratio.iloc[-1] > self.volume_threshold,
                'volatility_valid': volatility.iloc[-1] < self.max_volatility
            }
            
        except Exception as e:
            self.logger.error(f"检查成交量和波动率失败: {str(e)}")
            return None
            
    def analyze(self, data):
        """Analyze data and generate trading signals"""
        try:
            if not self._validate_data(data):
                return None
                
            # Calculate all indicators
            trend = self.calculate_trend_indicators(data)
            entry = self.calculate_entry_triggers(data)
            stops = self.calculate_stop_levels(data)
            vol_check = self.check_volume_volatility(data)
            
            if any(x is None for x in [trend, entry, stops, vol_check]):
                return None
                
            # Get latest values
            latest = {
                'close': data['close'].iloc[-1],
                'macd_hist': trend['macd_hist'].iloc[-1],
                'trend_strength': trend['trend_strength'].iloc[-1],
                'rsi': entry['rsi'].iloc[-1],
                'stoch_k': entry['stoch_k'].iloc[-1],
                'stoch_d': entry['stoch_d'].iloc[-1],
                'alpha': entry['alpha'].iloc[-1],
                'stop_level': stops['final_stop'].iloc[-1],
                'volume_ratio': vol_check['volume_ratio'].iloc[-1],
                'volatility': vol_check['volatility'].iloc[-1]
            }
            
            # Count buy/sell signals
            buy_signals = 0
            sell_signals = 0
            
            # Trend signals
            if latest['macd_hist'] > 0 and latest['trend_strength'] > 0:
                buy_signals += 1
            elif latest['macd_hist'] < 0 and latest['trend_strength'] < 0:
                sell_signals += 1
                
            # Entry trigger signals
            if (latest['rsi'] < self.rsi_oversold and 
                latest['stoch_k'] > latest['stoch_d'] and
                latest['alpha'] > self.alpha_threshold):
                buy_signals += 1
            elif (latest['rsi'] > self.rsi_overbought and
                  latest['stoch_k'] < latest['stoch_d'] and
                  latest['alpha'] < -self.alpha_threshold):
                sell_signals += 1
                
            # Volume and volatility confirmation
            if vol_check['volume_valid'] and vol_check['volatility_valid']:
                buy_signals += 1
            elif not vol_check['volatility_valid']:
                sell_signals += 1
                
            # Generate final signal
            if buy_signals >= 2:  # Need at least 2 confirming signals
                signal = "买入"
            elif sell_signals >= 2:
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'signal': signal,
                'indicators': latest,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'stop_level': latest['stop_level']
            }
            
        except Exception as e:
            self.logger.error(f"分析失败: {str(e)}")
            return None
            
    def get_signals(self, data):
        """Get trading signals"""
        try:
            if len(data) < max(self.macd_slow, self.bb_period, self.atr_period):
                return []
                
            signals = []
            result = self.analyze(data)
            
            if result and result['signal'] != "无":
                signals.append({
                    'date': data.index[-1],
                    'type': result['signal'],
                    'strategy': self.name,
                    'price': data['close'].iloc[-1],
                    'stop_level': result['stop_level'],
                    'indicators': result['indicators'],
                    'buy_signals': result['buy_signals'],
                    'sell_signals': result['sell_signals']
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取信号失败: {str(e)}")
            return []
