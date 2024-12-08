# -*- encoding: UTF-8 -*-

import data_fetcher
import settings
import strategy.enter as enter
from strategy import turtle_trade, climax_limitdown
from strategy import backtrace_ma250
from strategy import breakthrough_platform
from strategy import parking_apron
from strategy import low_backtrace_increase
from strategy import keep_increasing
from strategy import high_tight_flag
from strategy import formulaic_alphas
from strategy import RARA
from strategy import alpha_factors101
from strategy import alpha_factors191
import akshare as ak
import push
import logging
import time
from datetime import datetime
from collections import defaultdict
import os
import pandas as pd
import numpy as np
import traceback
from logger_manager import LoggerManager

class WorkFlow:
    def __init__(self):
        self.logger_manager = LoggerManager()
        self.logger = self.logger_manager.get_logger("work_flow")

    def ensure_dir_exists(self, path):
        """确保目录存在"""
        if not os.path.exists(path):
            os.makedirs(path)

    def prepare_data(self, data):
        """准备数据"""
        try:
            if data is None or data.empty:
                return None
            
            # 确保数据类型正确
            numeric_columns = ['开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅']
            for col in numeric_columns:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
            
            # 计算技术指标
            data['MA5'] = data['收盘'].rolling(window=5).mean()
            data['MA10'] = data['收盘'].rolling(window=10).mean()
            data['MA20'] = data['收盘'].rolling(window=20).mean()
            data['MA30'] = data['收盘'].rolling(window=30).mean()
            data['MA60'] = data['收盘'].rolling(window=60).mean()
            data['MA250'] = data['收盘'].rolling(window=250).mean()
            
            data['VOL_MA5'] = data['成交量'].rolling(window=5).mean()
            data['VOL_MA10'] = data['成交量'].rolling(window=10).mean()
            data['VOL_MA20'] = data['成交量'].rolling(window=20).mean()
            
            # 计算其他指标
            data['ATR'] = self.calculate_atr(data)
            data['波动率'] = self.calculate_volatility(data)
            
            return data
            
        except Exception as e:
            self.logger.error(f"准备数据时出错: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return None

    def calculate_atr(self, data, period=14):
        """计算ATR指标"""
        try:
            high = data['最高']
            low = data['最低']
            close = data['收盘']
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            
            return atr
            
        except Exception as e:
            self.logger.error(f"计算ATR时出错: {str(e)}")
            return pd.Series(index=data.index)

    def calculate_volatility(self, data, period=20):
        """计算波动率"""
        try:
            returns = data['收盘'].pct_change()
            volatility = returns.rolling(window=period).std() * np.sqrt(period)
            return volatility
            
        except Exception as e:
            self.logger.error(f"计算波动率时出错: {str(e)}")
            return pd.Series(index=data.index)

    def analyze_stock(self, code, data):
        """分析单只股票"""
        try:
            # 准备数据
            processed_data = self.prepare_data(data)
            if processed_data is None:
                self.logger.warning(f"股票{code}数据处理失败")
                return []
            
            # 运行策略分析
            strategies = {
                '放量上涨': enter.check_volume,
                '均线多头': keep_increasing.check,
                '停机坪': parking_apron.check,
                '回踩年线': backtrace_ma250.check,
                '无大幅回撤': low_backtrace_increase.check,
                '海龟交易法则': turtle_trade.check_enter,
                '高而窄的旗形': high_tight_flag.check,
                '放量跌停': climax_limitdown.check,
                'RARA策略': RARA.check,
                'Alpha因子策略': formulaic_alphas.check,
            }
            
            results = []
            for strategy_name, strategy_func in strategies.items():
                try:
                    if strategy_func(code, processed_data):
                        results.append((strategy_name, "买入"))
                except Exception as e:
                    self.logger.error(f"运行策略{strategy_name}时出错: {str(e)}")
                    self.logger.debug(traceback.format_exc())
            
            return results
            
        except Exception as e:
            self.logger.error(f"分析股票{code}时出错: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return []

    def analyze_stocks(self, stocks_data):
        """分析多只股票"""
        results = {}
        
        try:
            for code, data in stocks_data.items():
                results[code] = self.analyze_stock(code, data)
            
            return results
            
        except Exception as e:
            self.logger.error(f"批量分析股票时出错: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return results

    def prepare(self):
        """主工作流程"""
        try:
            self.logger.info("开始执行工作流程")
            # 确保目录存在
            self.ensure_dir_exists('results')
            self.ensure_dir_exists('logs')
            
            # 获取股票数据
            stocks_data = data_fetcher.run()
            if not stocks_data:
                self.logger.error("未获取到股票数据")
                return
            
            # 分析股票
            results = self.analyze_stocks(stocks_data)
            
            # 导出结果
            self.export_results(results, stocks_data)
            
        except Exception as e:
            self.logger.error(f"工作流程出错: {str(e)}")
            self.logger.debug(traceback.format_exc())

    def setup_logging(self):
        """设置日志系统"""
        # 已由LoggerManager处理
        pass

    def export_results(self, results, stocks_data):
        """导出分析结果"""
        try:
            self.logger.info("开始导出分析结果")
            
            # 创建结果目录
            result_dir = self.logger_manager.create_result_subdirectory('analysis')
            
            # 导出为CSV
            result_file = os.path.join(result_dir, 'analysis_results.csv')
            
            # 整理结果数据
            rows = []
            for code, strategies in results.items():
                if strategies:  # 只导出有策略信号的股票
                    for strategy, signal in strategies:
                        rows.append({
                            '股票代码': code,
                            '策略名称': strategy,
                            '信号类型': signal,
                            '分析时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
            
            if rows:
                df = pd.DataFrame(rows)
                df.to_csv(result_file, index=False, encoding='utf-8-sig')
                self.logger.info(f"分析结果已保存到: {result_file}")
            else:
                self.logger.warning("没有产生任何分析结果")
                
        except Exception as e:
            self.logger.error(f"导出结果失败: {str(e)}")
            self.logger.debug(traceback.format_exc())
            raise

    def run(self):
        """运行工作流程（与prepare方法相同）"""
        self.prepare()


