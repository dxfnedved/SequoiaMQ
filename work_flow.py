# -*- encoding: UTF-8 -*-

import data_fetcher
import settings
import os
import pandas as pd
import numpy as np
from datetime import datetime
from logger_manager import LoggerManager
from strategy.RSRS import RSRS_Strategy
from strategy.alpha_factors101 import Alpha101Strategy

class WorkFlow:
    """工作流程管理"""
    def __init__(self, strategies=None, logger_manager=None):
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("work_flow")
        
        # 初始化组件
        self.data_fetcher = data_fetcher.DataFetcher(logger_manager=self.logger_manager)
        
        # 初始化策略
        self.strategies = []
        if strategies:
            for strategy_info in strategies:
                try:
                    strategy_instance = strategy_info['class']()
                    self.strategies.append({
                        'name': strategy_info['name'],
                        'instance': strategy_instance
                    })
                except Exception as e:
                    self.logger.error(f"初始化策略 {strategy_info['name']} 失败: {str(e)}")
        
    def get_stock_data(self, code):
        """获取股票数据"""
        try:
            return self.data_fetcher.fetch_stock_data(code)
        except Exception as e:
            self.logger.error(f"获取股票数据失败: {str(e)}")
            return None
            
    def get_stock_signals(self, code):
        """获取股票买卖信号"""
        try:
            data = self.get_stock_data(code)
            if data is None:
                return []
                
            signals = []
            
            # 获取各个策略的信号
            for strategy in self.strategies:
                try:
                    strategy_signals = strategy['instance'].get_signals(data)
                    signals.extend(strategy_signals)
                except Exception as e:
                    self.logger.error(f"获取策略 {strategy['name']} 信号失败: {str(e)}")
            
            return signals
            
        except Exception as e:
            self.logger.error(f"获取股票信号失败: {str(e)}")
            return []
            
    def analyze_stock(self, code):
        """分析股票"""
        try:
            data = self.get_stock_data(code)
            if data is None:
                return None
                
            results = {}
            
            # 运行各个策略的分析
            for strategy in self.strategies:
                try:
                    result = strategy['instance'].analyze(data)
                    if result:
                        # 将策略名称添加到结果键中
                        strategy_results = {
                            f"{strategy['name']}_{key}": value 
                            for key, value in result.items()
                        }
                        results.update(strategy_results)
                except Exception as e:
                    self.logger.error(f"策略 {strategy['name']} 分析失败: {str(e)}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"分析股票失败: {str(e)}")
            return None

    def prepare(self):
        """准备数据和执行分析"""
        try:
            # 获取股票列表
            stock_list = settings.top_list
            if not stock_list:
                self.logger.error("股票列表为空")
                return
            
            # 获取数据（使用多线程）
            self.logger.info("开始获取股票数据...")
            stocks_data = self.data_fetcher.run(stock_list)
            if not stocks_data:
                self.logger.error("未能获取到任何股票数据")
                return
            
            # 分析每只股票
            self.logger.info(f"开始分析 {len(stocks_data)} 只股票...")
            results = {}
            with tqdm(total=len(stocks_data), desc="分析进度") as pbar:
                for code, data in stocks_data.items():
                    result = self.analyze_stock(code, data)
                    if result:
                        results[code] = result
                    pbar.update(1)
            
            # 保存结果
            self.save_results(results)
            
        except Exception as e:
            self.logger.error(f"工作流执行失败: {str(e)}")

    def calculate_basic_indicators(self, data):
        """计算基本技术指标"""
        try:
            result = {}
            
            # 计算最新价格和涨跌幅
            latest_price = data['Close'].iloc[-1]
            price_change = data['Change'].iloc[-1]
            
            # 计算均线
            for period in [5, 10, 20, 30, 60, 250]:
                ma = data['Close'].rolling(window=period).mean().iloc[-1]
                result[f'MA{period}'] = round(ma, 2)
            
            # 计算成交量指标
            volume = data['Volume'].iloc[-1]
            vol_ma5 = data['Volume'].rolling(window=5).mean().iloc[-1]
            vol_ma10 = data['Volume'].rolling(window=10).mean().iloc[-1]
            
            # 计算波动率
            returns = data['Close'].pct_change()
            volatility = returns.std() * np.sqrt(252)
            
            # 计算ATR
            tr1 = data['High'] - data['Low']
            tr2 = abs(data['High'] - data['Close'].shift(1))
            tr3 = abs(data['Low'] - data['Close'].shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean().iloc[-1]
            
            # 汇总结果
            result.update({
                '最新价格': round(latest_price, 2),
                '涨跌幅': round(price_change, 2),
                '成交量': round(volume/10000, 2),
                '量比': round(volume/vol_ma5, 2),
                '波动率': round(volatility * 100, 2),
                'ATR': round(atr, 2)
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"计算基本指标失败: {str(e)}")
            return {}

    def save_results(self, results):
        """保存分析结果"""
        try:
            if not results:
                self.logger.warning("没有结果可保存")
                return
            
            # 创建结果目录
            result_dir = "results"
            os.makedirs(result_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(result_dir, f"analysis_{timestamp}.xlsx")
            
            # 转换结果为DataFrame
            rows = []
            for code, result in results.items():
                row = {'股票代码': code, '分析时间': timestamp}
                row.update(result)
                rows.append(row)
            
            df = pd.DataFrame(rows)
            
            # 保存到Excel
            df.to_excel(filename, index=False)
            self.logger.info(f"分析结果已保存: {filename}")
            
            # 生成HTML报告
            self.generate_html_report(df, timestamp)
            
        except Exception as e:
            self.logger.error(f"保存结果失败: {str(e)}")

    def generate_html_report(self, df, timestamp):
        """生成HTML分析报告"""
        try:
            # 创建HTML文件
            report_file = os.path.join("results", f"report_{timestamp}.html")
            
            # 生成HTML内容
            html_content = f"""
            <html>
            <head>
                <title>股票分析报告 - {timestamp}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f5f5f5; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .signal {{ color: #e91e63; font-weight: bold; }}
                </style>
            </head>
            <body>
                <h1>股票分析报告</h1>
                <p>生成时间: {timestamp}</p>
                {df.to_html(classes='table', escape=False)}
            </body>
            </html>
            """
            
            # 保存HTML文件
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML报告已保存到: {report_file}")
            
        except Exception as e:
            self.logger.error(f"生成HTML报告失败: {str(e)}")

    def ensure_dir_exists(self, path):
        """确保目录存在"""
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            self.logger.error(f"创建目录失败: {str(e)}")
            raise


