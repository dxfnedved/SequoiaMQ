# -*- encoding: UTF-8 -*-

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import akshare as ak
from strategy.base import BaseStrategy
from logger_manager import LoggerManager
import math

class Alpha191Strategy(BaseStrategy):
    """Alpha191策略"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "Alpha191Strategy"
        self.window_size = 250  # 回溯窗口大小
        self.predict_period = 2  # 预测周期
        self.transaction_cost = 0.003  # 交易成本
        self.industry_exposure = 0.05  # 行业敞口限制
        self.style_exposure = 0.1  # 风格敞口限制
        self.benchmark = '000905.SH'  # 中证500指数
        
        # 设置半衰期参数
        self.beta_halflife = 60  # Beta因子半衰期
        self.momentum_halflife = 120  # 动量因子半衰期
        self.vol_halflife = 40  # 波动率因子半衰期
        
    def get_hs300_data(self):
        """获取沪深300指数数据"""
        try:
            hs300_data = ak.stock_zh_index_daily(symbol="sh000300")
            hs300_data.index = pd.to_datetime(hs300_data['date'])
            return hs300_data
        except Exception as e:
            self.logger.error(f"获取沪深300数据失败: {str(e)}")
            return None
            
    def calculate_exponential_weights(self, window, halflife):
        """计算指数衰减权重"""
        weights = np.exp(-np.log(2) / halflife * np.arange(window))
        return weights / weights.sum()
        
    def calculate_beta(self, data):
        """计算Beta因子"""
        try:
            # 获取沪深300数据
            hs300_data = self.get_hs300_data()
            if hs300_data is None:
                return 0
                
            # 计算收益率
            stock_returns = data['收盘'].pct_change()
            hs300_returns = hs300_data['close'].pct_change()
            
            # 计算指数衰减权重
            weights = self.calculate_exponential_weights(250, self.beta_halflife)
            
            # 加权回归
            X = hs300_returns.values[-250:].reshape(-1, 1)
            y = stock_returns.values[-250:]
            
            model = LinearRegression()
            model.fit(X, y, sample_weight=weights)
            
            return model.coef_[0]
        except Exception as e:
            self.logger.error(f"计算Beta失败: {str(e)}")
            return 0
            
    def calculate_momentum_rstr(self, data):
        """计算动量因子RSTR"""
        try:
            returns = data['收盘'].pct_change()
            weights = self.calculate_exponential_weights(120, self.momentum_halflife)
            weighted_returns = (returns.iloc[-120:] * weights).sum()
            return weighted_returns
        except Exception as e:
            self.logger.error(f"计算RSTR失败: {str(e)}")
            return 0
            
    def calculate_size_lncap(self, data):
        """计算规模因子LNCAP"""
        try:
            market_cap = data['收盘'] * data['成交量']  # 简化计算，实际应使用总股本
            return np.log(market_cap.iloc[-1])
        except Exception as e:
            self.logger.error(f"计算LNCAP失败: {str(e)}")
            return 0
            
    def calculate_earnings_factors(self, data, code):
        """计算盈利类因子"""
        try:
            # 获取财务数据
            financial_data = ak.stock_financial_analysis_indicator(symbol=code)
            
            # EPIBS - 一致预期每股收益
            eps_forecast = financial_data['基本每股收益'].iloc[-1]
            
            # ETOP - 历史EP值
            net_profit = financial_data['净利润'].iloc[-12:].sum()
            market_cap = data['收盘'].iloc[-1] * data['成交量'].iloc[-1]
            etop = net_profit / market_cap if market_cap != 0 else 0
            
            # CETOP - 现金收益比
            cash_flow = financial_data['经营活动产生的现金流量净额'].iloc[-4:].sum()
            cetop = cash_flow / market_cap if market_cap != 0 else 0
            
            return {
                'epibs': eps_forecast,
                'etop': etop,
                'cetop': cetop
            }
        except Exception as e:
            self.logger.error(f"计算盈利因子失败: {str(e)}")
            return {'epibs': 0, 'etop': 0, 'cetop': 0}
            
    def calculate_volatility_factors(self, data):
        """计算波动率因子"""
        try:
            returns = data['收盘'].pct_change()
            
            # DASTD - 衰减波动率
            weights = self.calculate_exponential_weights(250, self.vol_halflife)
            dastd = np.sqrt((returns.iloc[-250:] ** 2 * weights).sum())
            
            # CMRA - 累积范围波动率
            monthly_returns = returns.resample('M').sum()
            cmra = np.log(1 + monthly_returns.max()) - np.log(1 + monthly_returns.min())
            
            # HSIGMA - 特异波动率
            beta = self.calculate_beta(data)
            hs300_returns = self.get_hs300_data()['close'].pct_change()
            residuals = returns - beta * hs300_returns
            hsigma = residuals.std()
            
            return {
                'dastd': dastd,
                'cmra': cmra,
                'hsigma': hsigma
            }
        except Exception as e:
            self.logger.error(f"计算波动率因子失败: {str(e)}")
            return {'dastd': 0, 'cmra': 0, 'hsigma': 0}
            
    def calculate_growth_factors(self, code):
        """计算成长因子"""
        try:
            # 获取财务数据
            financial_data = ak.stock_financial_analysis_indicator(symbol=code)
            
            # SGRO - 营收增长率
            revenue = financial_data['营业收入'].iloc[-20:]  # 5年数据
            sgro = (revenue.iloc[-1] / revenue.iloc[0]) ** (1/5) - 1
            
            # EGRO - 净利润增长率
            net_profit = financial_data['净利润'].iloc[-20:]
            egro = (net_profit.iloc[-1] / net_profit.iloc[0]) ** (1/5) - 1
            
            # 获取预期数据（简化处理）
            egib = 0  # 需要从其他数据源获取
            egib_s = 0  # 需要从其他数据源获取
            
            return {
                'sgro': sgro,
                'egro': egro,
                'egib': egib,
                'egib_s': egib_s
            }
        except Exception as e:
            self.logger.error(f"计算成长因子失败: {str(e)}")
            return {'sgro': 0, 'egro': 0, 'egib': 0, 'egib_s': 0}
            
    def calculate_value_btop(self, data, code):
        """计算价值因子BTOP"""
        try:
            financial_data = ak.stock_financial_analysis_indicator(symbol=code)
            total_equity = financial_data['所有者权益'].iloc[-1]
            market_cap = data['收盘'].iloc[-1] * data['成交量'].iloc[-1]
            return total_equity / market_cap if market_cap != 0 else 0
        except Exception as e:
            self.logger.error(f"计算BTOP失败: {str(e)}")
            return 0
            
    def calculate_leverage_factors(self, code):
        """计算杠杆因子"""
        try:
            financial_data = ak.stock_financial_analysis_indicator(symbol=code)
            
            # MLEV - 市场杠杆
            market_cap = financial_data['总市值'].iloc[-1]
            total_debt = financial_data['总负债'].iloc[-1]
            mlev = (market_cap + total_debt) / market_cap if market_cap != 0 else 0
            
            # DTOA - 资产负债率
            total_assets = financial_data['总资产'].iloc[-1]
            dtoa = total_debt / total_assets if total_assets != 0 else 0
            
            # BLEV - 账面杠杆
            total_equity = financial_data['所有者权益'].iloc[-1]
            blev = total_assets / total_equity if total_equity != 0 else 0
            
            return {
                'mlev': mlev,
                'dtoa': dtoa,
                'blev': blev
            }
        except Exception as e:
            self.logger.error(f"计算杠杆因子失败: {str(e)}")
            return {'mlev': 0, 'dtoa': 0, 'blev': 0}
            
    def calculate_liquidity_factors(self, data):
        """计算流动性因子"""
        try:
            volume = data['成交量']
            
            # STOM - 月换手率
            stom = volume.iloc[-20:].sum() / volume.iloc[-1]
            
            # STOQ - 季换手率
            stoq = volume.iloc[-60:].sum() / volume.iloc[-1]
            
            # STOA - 年换手率
            stoa = volume.iloc[-250:].sum() / volume.iloc[-1]
            
            return {
                'stom': stom,
                'stoq': stoq,
                'stoa': stoa
            }
        except Exception as e:
            self.logger.error(f"计算流动性因子失败: {str(e)}")
            return {'stom': 0, 'stoq': 0, 'stoa': 0}
            
    def analyze(self, data):
        """分析数据"""
        try:
            if len(data) < self.window_size:
                return None
                
            code = data.index[-1].split('.')[0]  # 获取股票代码
            
            # 计算各类因子
            beta = self.calculate_beta(data)
            momentum = self.calculate_momentum_rstr(data)
            size = self.calculate_size_lncap(data)
            earnings = self.calculate_earnings_factors(data, code)
            volatility = self.calculate_volatility_factors(data)
            growth = self.calculate_growth_factors(code)
            value = self.calculate_value_btop(data, code)
            leverage = self.calculate_leverage_factors(code)
            liquidity = self.calculate_liquidity_factors(data)
            
            # 构建因子矩阵
            factor_values = {
                'beta': beta,
                'momentum': momentum,
                'size': size,
                'epibs': earnings['epibs'],
                'etop': earnings['etop'],
                'cetop': earnings['cetop'],
                'dastd': volatility['dastd'],
                'cmra': volatility['cmra'],
                'hsigma': volatility['hsigma'],
                'sgro': growth['sgro'],
                'egro': growth['egro'],
                'egib': growth['egib'],
                'egib_s': growth['egib_s'],
                'btop': value,
                'mlev': leverage['mlev'],
                'dtoa': leverage['dtoa'],
                'blev': leverage['blev'],
                'stom': liquidity['stom'],
                'stoq': liquidity['stoq'],
                'stoa': liquidity['stoa']
            }
            
            # 因子标准化
            factor_df = pd.DataFrame([factor_values])
            normalized_factors = StandardScaler().fit_transform(factor_df)
            
            # 计算综合得分
            weights = np.ones(len(factor_values)) / len(factor_values)  # 等权重
            score = np.dot(normalized_factors[0], weights)
            
            # 生成信号
            current_price = data['收盘'].iloc[-1]
            prev_price = data['收盘'].iloc[-2]
            
            if score > 0.1 and current_price > prev_price:  # 阈值可调整
                signal = "买入"
            elif score < -0.1 and current_price < prev_price:
                signal = "卖出"
            else:
                signal = "无"
                
            return {
                'signal': signal,
                'score': score,
                'factors': factor_values
            }
            
        except Exception as e:
            self.logger.error(f"Alpha191策略分析失败: {str(e)}")
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
                    'score': result['score'],
                    'factors': result['factors']
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取Alpha191策略信号失败: {str(e)}")
            return [] 