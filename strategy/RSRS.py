import numpy as np
import pandas as pd
from strategy.base import BaseStrategy

class RSRS_Strategy(BaseStrategy):
    """阻力支撑相对强度策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "RSRS_Strategy"
        self.window_size = 18  # 计算斜率的窗口大小
        self.score_threshold = 0.7  # 标准分阈值
        
    def calculate_rsrs(self, data):
        """计算RSRS指标"""
        try:
            high = data['最高'].values
            low = data['最低'].values
            
            # 使用最近window_size天的数据计算斜率
            x = low[-self.window_size:]
            y = high[-self.window_size:]
            
            # 计算线性回归
            slope, intercept = np.polyfit(x, y, 1)
            
            # 计算R方
            y_pred = slope * x + intercept
            r2 = 1 - (sum((y - y_pred) ** 2) / ((len(y) - 1) * np.var(y, ddof=1)))
            
            # 计算标准化得分
            score = slope * r2
            
            return slope, score
            
        except Exception as e:
            print(f"计算RSRS指标失败: {str(e)}")
            return None, None
        
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.window_size:
                return None
                
            # 计算RSRS指标
            slope, score = self.calculate_rsrs(data)
            if slope is None or score is None:
                return None
                
            # 判断信号
            if score > self.score_threshold:
                signal = "买入"
            elif score < -self.score_threshold:
                signal = "卖出"
            else:
                signal = "无"
                
            # 计算支撑和阻力位
            support = data['最低'].rolling(window=self.window_size).min().iloc[-1]
            resistance = data['最高'].rolling(window=self.window_size).max().iloc[-1]
                
            return {
                'slope': slope,  # 斜率
                'score': score,  # RSRS标准分
                'support': support,  # 支撑位
                'resistance': resistance,  # 阻力位
                'signal': signal  # 信号
            }
            
        except Exception as e:
            print(f"RSRS策略分析失败: {str(e)}")
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
                    'slope': result['slope'],
                    'score': result['score'],
                    'support': result['support'],
                    'resistance': result['resistance']
                })
                
            return signals
            
        except Exception as e:
            print(f"获取RSRS策略信号失败: {str(e)}")
            return []