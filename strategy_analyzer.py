import pandas as pd
import numpy as np
from strategy.RARA import RARA_Strategy
from logger_manager import LoggerManager

class StrategyAnalyzer:
    """策略分析器类"""
    def __init__(self, logger_manager=None):
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("strategy_analyzer")
        
        # 初始化策略
        self.strategies = {
            'RARA': RARA_Strategy(logger_manager=self.logger_manager)
        }

    def analyze_stocks(self, data_list):
        """分析多个股票数据"""
        try:
            if not data_list:
                self.logger.error("没有数据可供分析")
                return []

            results = []
            for data in data_list:
                if data is None or data.empty:
                    self.logger.warning("跳过空数据")
                    continue

                result = self.analyze_single_stock(data)
                if result:
                    results.append(result)

            return results

        except Exception as e:
            self.logger.error(f"分析股票数据失败: {str(e)}")
            return []

    def analyze_single_stock(self, data):
        """分析单个股票数据"""
        try:
            if data is None or data.empty:
                self.logger.error("数据为空，无法分析")
                return None

            result = {}
            
            # 计算基本指标
            result.update(self.calculate_basic_indicators(data))
            
            # 运行RARA策略
            rara_result = self.strategies['RARA'].analyze(data)
            if rara_result:
                result.update(rara_result)

            return result

        except Exception as e:
            self.logger.error(f"分析单个股票失败: {str(e)}")
            return None

    def calculate_basic_indicators(self, data):
        """计算基本技术指标"""
        try:
            result = {}
            
            # 计算最新价格和涨跌幅
            latest_price = data['Close'].iloc[-1]
            price_change = data['Change'].iloc[-1]
            
            # 计算均线
            ma5 = data['Close'].rolling(window=5).mean().iloc[-1]
            ma10 = data['Close'].rolling(window=10).mean().iloc[-1]
            ma20 = data['Close'].rolling(window=20).mean().iloc[-1]
            
            # 计算成交量变化
            vol_ma5 = data['Volume'].rolling(window=5).mean().iloc[-1]
            current_vol = data['Volume'].iloc[-1]
            vol_ratio = current_vol / vol_ma5 if vol_ma5 != 0 else 0
            
            # 计算波动率
            volatility = data['Close'].pct_change().std() * np.sqrt(252) * 100
            
            # 汇总结果
            result.update({
                '最新价格': round(latest_price, 2),
                '涨跌幅': round(price_change, 2),
                'MA5': round(ma5, 2),
                'MA10': round(ma10, 2),
                'MA20': round(ma20, 2),
                '量比': round(vol_ratio, 2),
                '波动率': round(volatility, 2)
            })
            
            # 添加技术分析结论
            result.update(self.generate_technical_analysis(data))
            
            return result
            
        except Exception as e:
            self.logger.error(f"计算基本指标失败: {str(e)}")
            return {}

    def generate_technical_analysis(self, data):
        """生成技术分析结论"""
        try:
            result = {}
            
            # 获取最新数据
            latest = data.iloc[-1]
            prev = data.iloc[-2]
            
            # ���势判断
            ma5 = data['Close'].rolling(window=5).mean()
            ma10 = data['Close'].rolling(window=10).mean()
            ma20 = data['Close'].rolling(window=20).mean()
            
            trend = "盘整"
            if ma5.iloc[-1] > ma10.iloc[-1] > ma20.iloc[-1]:
                trend = "上升"
            elif ma5.iloc[-1] < ma10.iloc[-1] < ma20.iloc[-1]:
                trend = "下降"
            
            # 成交量分析
            vol_trend = "正常"
            if latest['Volume'] > data['Volume'].rolling(window=5).mean().iloc[-1] * 1.5:
                vol_trend = "放量"
            elif latest['Volume'] < data['Volume'].rolling(window=5).mean().iloc[-1] * 0.5:
                vol_trend = "缩量"
            
            # 价格突破分析
            breakthrough = "无"
            if latest['Close'] > ma20.iloc[-1] and prev['Close'] <= ma20.iloc[-1]:
                breakthrough = "向上突破MA20"
            elif latest['Close'] < ma20.iloc[-1] and prev['Close'] >= ma20.iloc[-1]:
                breakthrough = "向下跌破MA20"
            
            result.update({
                '趋势': trend,
                '成交量': vol_trend,
                '突破': breakthrough
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"生成技术分析结论失败: {str(e)}")
            return {} 