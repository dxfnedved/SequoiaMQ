import numpy as np
import pandas as pd
import talib as ta
from strategy.base import BaseStrategy

class RSRS_Strategy(BaseStrategy):
    """RSRS择时策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "RSRS_Strategy"
        self.window_size = 20  # 观察窗口
        self.rsi_threshold = 50  # RSI阈值
        self.rsrs_threshold = 0.7  # RSRS阈值
        
    def calculate_rsrs(self, data, window_size=16):
        """计算RSRS指标"""
        try:
            # 准备数据
            high = data['high'].values
            low = data['low'].values
            
            # 计算斜率和R²
            slopes = []
            r2s = []
            
            for i in range(len(data) - window_size + 1):
                x = low[i:i+window_size]
                y = high[i:i+window_size]
                
                if len(x) < window_size:
                    continue
                    
                # 添加常数项
                X = np.column_stack([np.ones_like(x), x])
                
                # 最小二乘法
                try:
                    beta = np.linalg.lstsq(X, y, rcond=None)[0]
                    y_pred = np.dot(X, beta)
                    
                    # 计算R²，避免除零
                    y_mean = y.mean()
                    ss_tot = np.sum((y - y_mean) ** 2)
                    ss_res = np.sum((y - y_pred) ** 2)
                    
                    if ss_tot == 0:  # 如果总离差平方和为0
                        r2 = 0  # 说明所有值都相同，设置R²为0
                    else:
                        r2 = 1 - ss_res / ss_tot
                        
                    slopes.append(beta[1])
                    r2s.append(r2)
                    
                except Exception as e:
                    self.logger.warning(f"计算RSRS指标失败: {str(e)}")
                    slopes.append(np.nan)
                    r2s.append(np.nan)
                    
            return np.array(slopes), np.array(r2s)
            
        except Exception as e:
            self.logger.error(f"RSRS指标计算失败: {str(e)}")
            return np.array([]), np.array([])
            
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.window_size * 2:
                return None
                
            # 计算RSRS指标
            slopes, r2s = self.calculate_rsrs(data)
            if len(slopes) == 0:
                return None
                
            # 获取最新值
            latest_slope = slopes[-1]
            latest_r2 = r2s[-1]
            
            # 计算支撑和阻力位
            support = data['low'].rolling(window=20).min().iloc[-1]
            resistance = data['high'].rolling(window=20).max().iloc[-1]
            
            # 计算RSI
            rsi = ta.RSI(data['close'].values, timeperiod=14)[-1]
            
            # 标准化RSRS指标
            slopes_series = pd.Series(slopes)
            mean = slopes_series.rolling(window=self.window_size).mean().iloc[-1]
            std = slopes_series.rolling(window=self.window_size).std().iloc[-1]
            
            if std != 0:
                zscore = (latest_slope - mean) / std
            else:
                zscore = 0
                
            # 右偏RSRS标准分
            rsrs_score = zscore * latest_r2
            
            # 判断信号
            if (rsrs_score > self.rsrs_threshold and
                rsi < self.rsi_threshold):
                signal = "买入"
            elif (rsrs_score < -self.rsrs_threshold and
                  rsi > 100 - self.rsi_threshold):
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'rsrs': rsrs_score,
                'rsi': rsi,
                'support': support,
                'resistance': resistance,
                'signal': signal,
                'factors': {
                    'slope': latest_slope,
                    'r2': latest_r2,
                    'zscore': zscore
                }
            }
            
        except Exception as e:
            self.logger.error(f"RSRS策略分析失败: {str(e)}")
            return None
            
    def get_signals(self, data):
        """获取买卖信号"""
        try:
            if len(data) < self.window_size * 2:
                return []
                
            signals = []
            result = self.analyze(data)
            
            if result and result['signal'] != "无":
                signals.append({
                    'date': data.index[-1],
                    'type': result['signal'],
                    'strategy': self.name,
                    'price': data['close'].iloc[-1],
                    'rsrs': result['rsrs'],
                    'rsi': result['rsi'],
                    'support': result['support'],
                    'resistance': result['resistance'],
                    'factors': result['factors']
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取RSRS策略信号失败: {str(e)}")
            return []