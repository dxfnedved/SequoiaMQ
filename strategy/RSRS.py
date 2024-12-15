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
        
    def calculate_rsrs(self, data):
        """计算RSRS指标"""
        try:
            high = data['high']  # Changed from '最高' to 'high'
            low = data['low']    # Changed from '最低' to 'low'
            
            # 计算斜率序列
            slopes = []
            r2_list = []
            for i in range(len(data) - self.window_size + 1):
                x = low.iloc[i:i+self.window_size].values.reshape(-1, 1)
                y = high.iloc[i:i+self.window_size].values
                
                # 添加常数项
                X = np.hstack([np.ones_like(x), x])
                
                # 计算回归系数
                try:
                    beta = np.linalg.inv(X.T @ X) @ X.T @ y
                    slope = beta[1]
                    
                    # 计算R方
                    y_pred = X @ beta
                    r2 = 1 - np.sum((y - y_pred) ** 2) / np.sum((y - y.mean()) ** 2)
                    
                    slopes.append(slope)
                    r2_list.append(r2)
                except:
                    slopes.append(np.nan)
                    r2_list.append(np.nan)
                    
            # 转换为Series
            slopes = pd.Series(slopes, index=data.index[self.window_size-1:])
            r2_list = pd.Series(r2_list, index=data.index[self.window_size-1:])
            
            # 标准化RSRS指标
            mean = slopes.rolling(window=self.window_size).mean()
            std = slopes.rolling(window=self.window_size).std()
            zscore = (slopes - mean) / std
            
            # 右偏RSRS标准分
            rsrs = zscore * r2_list
            
            return rsrs
            
        except Exception as e:
            self.logger.error(f"计算RSRS指标失败: {str(e)}")
            return None
            
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.window_size * 2:
                return None
                
            # 计算RSRS指标
            rsrs = self.calculate_rsrs(data)
            if rsrs is None:
                return None
                
            # 计算支撑和阻力位
            support = data['low'].rolling(window=20).min().iloc[-1]  # Changed from '最低' to 'low'
            resistance = data['high'].rolling(window=20).max().iloc[-1]  # Changed from '最高' to 'high'
            
            # 计算RSI
            rsi = ta.RSI(data['close'].values, timeperiod=14)[-1]
            
            # 获取最新值
            latest_rsrs = rsrs.iloc[-1]
            
            # 判断信号
            if (latest_rsrs > self.rsrs_threshold and
                rsi < self.rsi_threshold):
                signal = "买入"
            elif (latest_rsrs < -self.rsrs_threshold and
                  rsi > 100 - self.rsi_threshold):
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'rsrs': latest_rsrs,
                'rsi': rsi,
                'support': support,
                'resistance': resistance,
                'signal': signal
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
                    'price': data['close'].iloc[-1],  # Changed from '收盘' to 'close'
                    'rsrs': result['rsrs'],
                    'rsi': result['rsi'],
                    'support': result['support'],
                    'resistance': result['resistance']
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取RSRS策略信号失败: {str(e)}")
            return []