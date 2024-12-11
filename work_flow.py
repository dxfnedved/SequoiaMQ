# -*- encoding: UTF-8 -*-

import os
import json
import pandas as pd
from datetime import datetime
from data_fetcher import DataFetcher
from strategy_analyzer import StrategyAnalyzer
from logger_manager import LoggerManager

class WorkFlow:
    """工作流程类"""
    def __init__(self, logger_manager=None):
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("work_flow")
        
        # 初始化数据获取器和策略分析器
        self.data_fetcher = DataFetcher(logger_manager=self.logger_manager)
        self.strategy_analyzer = StrategyAnalyzer(logger_manager=self.logger_manager)
        
    def prepare(self):
        """准备工作"""
        try:
            print("开始准备工作...")
            self.logger.info("开始准备工作")
            
            # 创建必要的目录
            for dir_name in ['data', 'logs', 'cache']:
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)
                    print(f"创建目录: {dir_name}")
                    
            # 加载自选股列表
            watchlist_file = 'data/watchlist.json'
            if os.path.exists(watchlist_file):
                with open(watchlist_file, 'r', encoding='utf-8') as f:
                    watchlist = json.load(f)
                print(f"加载自选股列表: {len(watchlist)}只股票")
            else:
                watchlist = []
                print("未找到自选股列表，将分析所有A股")
                
            # 开始分析
            self.analyze_stocks(watchlist)
            
        except Exception as e:
            error_msg = f"准备工作失败: {str(e)}"
            print(error_msg)
            self.logger.error(error_msg)
            
    def analyze_stocks(self, watchlist=None):
        """分析股票"""
        try:
            # 如果没有自选股，获取所有A股
            if not watchlist:
                print("获取A股列表...")
                stock_list = self.data_fetcher.get_stock_list()
                print(f"获取到{len(stock_list)}只股票")
            else:
                stock_list = watchlist
                
            total = len(stock_list)
            print(f"\n开始分析{total}只股票...")
            
            # 分析每只股票
            for i, stock in enumerate(stock_list, 1):
                try:
                    code = stock['code'] if isinstance(stock, dict) else stock
                    print(f"\n[{i}/{total}] 分析股票 {code}")
                    
                    # 获取数据
                    print(f"获取{code}的历史数据...")
                    data = self.data_fetcher.get_stock_data(code)
                    if data is None or data.empty:
                        print(f"获取{code}数据失败，跳过")
                        continue
                        
                    # 分析数据
                    print(f"分析{code}的数据...")
                    result = self.strategy_analyzer.analyze(data, code)
                    
                    # 处理分析结果
                    if result:
                        # 保存分析结果
                        result_file = f'data/analysis_{code}_{datetime.now().strftime("%Y%m%d")}.json'
                        with open(result_file, 'w', encoding='utf-8') as f:
                            json.dump(result, f, indent=2, ensure_ascii=False)
                        print(f"保存{code}的分析结果到{result_file}")
                    else:
                        print(f"{code}没有产生分析结果")
                        
                except Exception as e:
                    error_msg = f"分析股票{code}时出错: {str(e)}"
                    print(error_msg)
                    self.logger.error(error_msg)
                    continue
                    
            print("\n所有股票分析完成!")
            
        except Exception as e:
            error_msg = f"分析股票失败: {str(e)}"
            print(error_msg)
            self.logger.error(error_msg)


