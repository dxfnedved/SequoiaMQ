import os
import sys
import unittest
import pandas as pd
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接从strategy包导入所有需要的类
from strategy import (
    BaseStrategy,
    RSRS_Strategy,
    Alpha101Strategy,
    Alpha191Strategy,
    TurtleStrategy,
    EnterStrategy,
    LowATRStrategy,
    LowBacktraceIncreaseStrategy,
    KeepIncreasingStrategy,
    BacktraceMA250Strategy
)

class TestStrategies(unittest.TestCase):
    """测试所有策略类"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建模拟数据
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        n = len(dates)
        
        # 生成价格数据
        open_prices = np.random.normal(100, 10, n).cumsum()
        high_prices = open_prices + np.abs(np.random.normal(2, 1, n))
        low_prices = open_prices - np.abs(np.random.normal(2, 1, n))
        close_prices = open_prices + np.random.normal(0, 2, n)
        
        # 确保价格的合理性
        high_prices = np.maximum(high_prices, np.maximum(open_prices, close_prices))
        low_prices = np.minimum(low_prices, np.minimum(open_prices, close_prices))
        
        # 生成成交量和成交额
        volume = np.abs(np.random.normal(1000000, 100000, n))
        amount = volume * close_prices
        
        self.test_data = pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volume,
            'amount': amount
        }, index=dates)
        
    def test_base_strategy(self):
        """测试基础策略类"""
        strategy = BaseStrategy()
        self.assertEqual(strategy.name, "BaseStrategy")
        with self.assertRaises(NotImplementedError):
            strategy.analyze(self.test_data)
        with self.assertRaises(NotImplementedError):
            strategy.get_signals(self.test_data)
            
    def test_rsrs_strategy(self):
        """测试RSRS策略"""
        strategy = RSRS_Strategy()
        self.assertEqual(strategy.name, "RSRS_Strategy")
        
        # 测试分析方法
        result = strategy.analyze(self.test_data)
        self.assertIsNotNone(result)
        self.assertIn('slope', result)
        self.assertIn('score', result)
        self.assertIn('support', result)
        self.assertIn('resistance', result)
        self.assertIn('signal', result)
        
        # 测试信号生成
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        for signal in signals:
            self.assertIn('date', signal)
            self.assertIn('type', signal)
            self.assertIn('strategy', signal)
            self.assertIn('price', signal)
            
    def test_alpha101_strategy(self):
        """测试Alpha101策略"""
        strategy = Alpha101Strategy()
        self.assertEqual(strategy.name, "Alpha101Strategy")
        
        # 测试分析方法
        result = strategy.analyze(self.test_data)
        self.assertIsNotNone(result)
        self.assertIn('alpha1', result)
        self.assertIn('alpha2', result)
        self.assertIn('alpha3', result)
        self.assertIn('alpha4', result)
        self.assertIn('signal', result)
        
        # 测试信号生成
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        for signal in signals:
            self.assertIn('date', signal)
            self.assertIn('type', signal)
            self.assertIn('strategy', signal)
            self.assertIn('price', signal)
            
    def test_alpha191_strategy(self):
        """测试Alpha191策略"""
        strategy = Alpha191Strategy()
        self.assertEqual(strategy.name, "Alpha191Strategy")
        
        # 测试分析方法
        result = strategy.analyze(self.test_data)
        self.assertIsNotNone(result)
        self.assertIn('alpha5', result)
        self.assertIn('alpha6', result)
        self.assertIn('alpha7', result)
        self.assertIn('alpha8', result)
        self.assertIn('signal', result)
        
        # 测试信号生成
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        for signal in signals:
            self.assertIn('date', signal)
            self.assertIn('type', signal)
            self.assertIn('strategy', signal)
            self.assertIn('price', signal)
            
    def test_turtle_strategy(self):
        """测试海龟交易策略"""
        strategy = TurtleStrategy()
        self.assertEqual(strategy.name, "TurtleStrategy")
        
        # 测试分析方法
        result = strategy.analyze(self.test_data)
        self.assertIsNotNone(result)
        self.assertIn('high_n', result)
        self.assertIn('low_n', result)
        self.assertIn('atr', result)
        self.assertIn('position_size', result)
        self.assertIn('signal', result)
        
        # 测试信号生成
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        for signal in signals:
            self.assertIn('date', signal)
            self.assertIn('type', signal)
            self.assertIn('strategy', signal)
            self.assertIn('price', signal)
            
    def test_enter_strategy(self):
        """测试入场策略"""
        strategy = EnterStrategy()
        self.assertEqual(strategy.name, "EnterStrategy")
        
        # 测试分析方法
        result = strategy.analyze(self.test_data)
        self.assertIsNotNone(result)
        self.assertIn('breakthrough', result)
        self.assertIn('volume_signal', result)
        self.assertIn('ma5', result)
        self.assertIn('ma10', result)
        self.assertIn('ma20', result)
        self.assertIn('signal', result)
        
        # 测试信号生成
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        for signal in signals:
            self.assertIn('date', signal)
            self.assertIn('type', signal)
            self.assertIn('strategy', signal)
            self.assertIn('price', signal)
            
    def test_low_atr_strategy(self):
        """测试低波动策略"""
        strategy = LowATRStrategy()
        self.assertEqual(strategy.name, "LowATRStrategy")
        
        # 测试分析方法
        result = strategy.analyze(self.test_data)
        self.assertIsNotNone(result)
        self.assertIn('atr', result)
        self.assertIn('atr_ratio', result)
        self.assertIn('ma20', result)
        self.assertIn('volume_ratio', result)
        self.assertIn('signal', result)
        
        # 测试信号生成
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        for signal in signals:
            self.assertIn('date', signal)
            self.assertIn('type', signal)
            self.assertIn('strategy', signal)
            self.assertIn('price', signal)
            
    def test_low_backtrace_increase_strategy(self):
        """测试低回撤增长策略"""
        strategy = LowBacktraceIncreaseStrategy()
        self.assertEqual(strategy.name, "LowBacktraceIncreaseStrategy")
        
        # 测试分析方法
        result = strategy.analyze(self.test_data)
        self.assertIsNotNone(result)
        self.assertIn('drawdown', result)
        self.assertIn('increase', result)
        self.assertIn('ma', result)
        self.assertIn('signal', result)
        
        # 测试信号生成
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        for signal in signals:
            self.assertIn('date', signal)
            self.assertIn('type', signal)
            self.assertIn('strategy', signal)
            self.assertIn('price', signal)
            
    def test_keep_increasing_strategy(self):
        """测试持续上涨策略"""
        strategy = KeepIncreasingStrategy()
        self.assertEqual(strategy.name, "KeepIncreasingStrategy")
        
        # 测试分析方法
        result = strategy.analyze(self.test_data)
        self.assertIsNotNone(result)
        self.assertIn('increase_days', result)
        self.assertIn('decrease_days', result)
        self.assertIn('period_returns', result)
        self.assertIn('max_drawdown', result)
        self.assertIn('signal', result)
        
        # 测试信号生成
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        for signal in signals:
            self.assertIn('date', signal)
            self.assertIn('type', signal)
            self.assertIn('strategy', signal)
            self.assertIn('price', signal)
            
    def test_backtrace_ma250_strategy(self):
        """测试回踩年线策略"""
        strategy = BacktraceMA250Strategy()
        self.assertEqual(strategy.name, "BacktraceMA250Strategy")
        
        # 测试分析方法
        result = strategy.analyze(self.test_data)
        self.assertIsNotNone(result)
        self.assertIn('ma250', result)
        self.assertIn('deviation', result)
        self.assertIn('volume_ratio', result)
        self.assertIn('rsi', result)
        self.assertIn('signal', result)
        
        # 测试信号生成
        signals = strategy.get_signals(self.test_data)
        self.assertIsInstance(signals, list)
        for signal in signals:
            self.assertIn('date', signal)
            self.assertIn('type', signal)
            self.assertIn('strategy', signal)
            self.assertIn('price', signal)

if __name__ == '__main__':
    unittest.main() 