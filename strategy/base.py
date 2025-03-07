# -*- encoding: UTF-8 -*-

import time
import numpy as np
import pandas as pd
from functools import lru_cache
from logger_manager import LoggerManager

class BaseStrategy:
    """策略基类"""
    def __init__(self, logger_manager=None):
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger(self.__class__.__name__)
        
        # 策略配置
        self.name = self.__class__.__name__
        self.description = "基础策略"
        self.version = "1.0.0"
        
        # 性能监控
        self._execution_times = []
        self._cache_hits = 0
        self._cache_misses = 0
        
        # 技术指标缓存
        self._indicator_cache = {}
        
    def analyze(self, data):
        """
        分析数据
        :param data: DataFrame 股票数据
        :return: dict 分析结果
        """
        # 记录执行时间
        start_time = time.time()
        
        try:
            # 验证数据
            if not self._validate_data(data):
                return None
                
            # 执行分析
            result = self._analyze_impl(data)
            
            # 添加元数据
            if result:
                result['strategy'] = self.name
                result['version'] = self.version
                
            return result
            
        except Exception as e:
            self.logger.error(f"策略分析失败: {str(e)}")
            return None
            
        finally:
            # 记录执行时间
            execution_time = time.time() - start_time
            self._execution_times.append(execution_time)
            
    def _analyze_impl(self, data):
        """
        实际的分析实现，子类应该重写此方法
        :param data: DataFrame 股票数据
        :return: dict 分析结果
        """
        raise NotImplementedError("子类必须实现_analyze_impl方法")
        
    def get_signals(self, data):
        """
        获取买卖信号
        :param data: DataFrame 股票数据
        :return: list 信号列表
        """
        # 记录执行时间
        start_time = time.time()
        
        try:
            # 验证数据
            if not self._validate_data(data):
                return []
                
            # 执行分析
            result = self.analyze(data)
            
            if not result:
                return []
                
            # 提取信号
            signals = self._extract_signals(data, result)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"获取信号失败: {str(e)}")
            return []
            
        finally:
            # 记录执行时间
            execution_time = time.time() - start_time
            self._execution_times.append(execution_time)
            
    def _extract_signals(self, data, result):
        """
        从分析结果中提取信号
        :param data: DataFrame 股票数据
        :param result: dict 分析结果
        :return: list 信号列表
        """
        signals = []
        
        if result and 'signal' in result and result['signal'] != "无":
            signals.append({
                'date': data.index[-1],
                'type': result['signal'],
                'strategy': self.name,
                'price': data['close'].iloc[-1],
                'factors': result.get('factors', {})
            })
            
        return signals
        
    def _validate_data(self, data):
        """
        验证数据有效性
        :param data: DataFrame 股票数据
        :return: bool 数据是否有效
        """
        try:
            if data is None or data.empty:
                self.logger.warning("数据为空")
                return False
                
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                self.logger.warning(f"数据缺少必要列: {missing_columns}")
                return False
            
            # 检查数据长度
            min_length = getattr(self, 'min_data_length', 20)
            if len(data) < min_length:
                self.logger.warning(f"数据长度不足: {len(data)} < {min_length}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"数据验证失败: {str(e)}")
            return False
            
    @lru_cache(maxsize=128)
    def _calculate_indicator(self, indicator_name, data_key, **params):
        """
        计算并缓存技术指标
        :param indicator_name: str 指标名称
        :param data_key: tuple 数据键（用于缓存）
        :param params: dict 计算参数
        :return: 计算结果
        """
        # 这里的data_key应该是一个可哈希的值，例如(code, date_str, len(data))
        cache_key = (indicator_name, data_key, frozenset(params.items()))
        
        if cache_key in self._indicator_cache:
            self._cache_hits += 1
            return self._indicator_cache[cache_key]
            
        self._cache_misses += 1
        
        # 根据指标名称调用相应的计算函数
        result = None
        
        # 存入缓存
        self._indicator_cache[cache_key] = result
        
        return result
        
    def get_performance_stats(self):
        """
        获取性能统计信息
        :return: dict 性能统计
        """
        execution_times = self._execution_times
        
        if not execution_times:
            return {
                'avg_execution_time': 0,
                'min_execution_time': 0,
                'max_execution_time': 0,
                'total_executions': 0,
                'cache_hits': self._cache_hits,
                'cache_misses': self._cache_misses,
                'cache_hit_ratio': 0
            }
            
        total_cache_requests = self._cache_hits + self._cache_misses
        cache_hit_ratio = self._cache_hits / total_cache_requests if total_cache_requests > 0 else 0
        
        return {
            'avg_execution_time': np.mean(execution_times),
            'min_execution_time': np.min(execution_times),
            'max_execution_time': np.max(execution_times),
            'total_executions': len(execution_times),
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_ratio': cache_hit_ratio
        }
        
    def clear_cache(self):
        """清除缓存"""
        self._indicator_cache.clear()
        self._calculate_indicator.cache_clear()
        
    def __str__(self):
        return f"{self.name} (v{self.version})"
        
    def __repr__(self):
        return f"{self.__class__.__name__}()" 