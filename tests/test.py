# -*- encoding: UTF-8 -*-

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_fetcher import DataFetcher
from strategy.alpha_factors101 import Alpha101Strategy
from strategy.alpha_factors191 import Alpha191Strategy
from strategy.RSRS import RSRSStrategy
from strategy.turtle_trade import TurtleStrategy
from strategy.low_atr import LowATRStrategy
from strategy.composite_strategy import CompositeStrategy
from strategy.backtrace_ma250 import BacktraceMA250Strategy

class TestDataFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = DataFetcher()
        
    def test_get_stock_list(self):
        stock_list = self.fetcher.get_stock_list()
        self.assertIsInstance(stock_list, list)
        if stock_list:
            self.assertIsInstance(stock_list[0], dict)
            self.assertIn('code', stock_list[0])
            self.assertIn('name', stock_list[0])
            
    def test_get_stock_data(self):
        # 测试获取平安银行的数据
        data = self.fetcher.get_stock_data('000001')
        self.assertIsInstance(data, pd.DataFrame)
        if not data.empty:
            self.assertGreater(len(data), 0)
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                self.assertIn(col, data.columns)
                
class TestStrategies(unittest.TestCase):
    def setUp(self):
        # 生成测试数据
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        n_days = len(dates)
        
        # 生成价格数据
        np.random.seed(42)
        base_price = 100
        daily_returns = np.random.normal(0.001, 0.02, n_days)
        prices = base_price * (1 + daily_returns).cumprod()
        
        # 添加一些趋势和波动
        trend = np.linspace(0, 0.5, n_days)
        prices = prices * (1 + trend)
        
        # 生成OHLC数据
        open_prices = prices * (1 + np.random.normal(0, 0.005, n_days))
        high_prices = np.maximum(prices * (1 + np.random.normal(0.005, 0.005, n_days)), open_prices)
        low_prices = np.minimum(prices * (1 + np.random.normal(-0.005, 0.005, n_days)), open_prices)
        close_prices = prices
        
        # 生成成交量和成交额
        volume = np.random.lognormal(10, 1, n_days)
        amount = close_prices * volume
        
        # 创建DataFrame
        self.test_data = pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volume,
            'amount': amount
        }, index=dates)
        
        # print(data['high'].values)  # Changed from '最高' to 'high'
        
    def test_alpha101_strategy(self):
        strategy = Alpha101Strategy()
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        
    def test_alpha191_strategy(self):
        strategy = Alpha191Strategy()
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        
    def test_rsrs_strategy(self):
        strategy = RSRSStrategy()
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        
    def test_turtle_strategy(self):
        strategy = TurtleStrategy()
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        
    def test_low_atr_strategy(self):
        strategy = LowATRStrategy()
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        
    def test_composite_strategy(self):
        strategy = CompositeStrategy()
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        
    def test_backtrace_ma250_strategy(self):
        strategy = BacktraceMA250Strategy()
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        
if __name__ == '__main__':
    unittest.main()