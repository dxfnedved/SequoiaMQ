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
import akshare as ak
import push
import logging
import time
from datetime import datetime
from collections import defaultdict
import os
import pandas as pd


def ensure_dir_exists(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)


class StrategyAnalyzer:
    def __init__(self, results_dir="results"):
        self.results_dir = results_dir
        self.date_str = datetime.now().strftime('%Y%m%d')
        ensure_dir_exists(results_dir)
        
    def analyze_strategy_confluence(self, stock_signals):
        """分析策略共振情况"""
        confluence_data = defaultdict(list)
        strategy_counts = defaultdict(int)
        
        # 统计每只股票的策略触发情况
        for code, signals in stock_signals.items():
            stock_code, stock_name = code
            triggered_strategies = [strategy for strategy, signal in signals if signal == "买入"]
            
            if triggered_strategies:  # 只记录有买入信号的股票
                strategy_count = len(triggered_strategies)
                strategy_counts[strategy_count] += 1
                
                confluence_data['日期'].append(self.date_str)
                confluence_data['股票代码'].append(stock_code)
                confluence_data['股票名称'].append(stock_name)
                confluence_data['触发策略数'].append(strategy_count)
                confluence_data['触发策略列表'].append(', '.join(triggered_strategies))
        
        # 保存共振分析结果
        if confluence_data:
            df = pd.DataFrame(confluence_data)
            # 按触发策略数降序排序
            df = df.sort_values('触发策略数', ascending=False)
            file_path = os.path.join(self.results_dir, f'strategy_confluence_{self.date_str}.csv')
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            # 保存共振统计信息
            stats_data = {
                '日期': [self.date_str] * len(strategy_counts),
                '触发策略数': list(strategy_counts.keys()),
                '股票数量': list(strategy_counts.values())
            }
            stats_df = pd.DataFrame(stats_data)
            stats_file = os.path.join(self.results_dir, f'confluence_statistics_{self.date_str}.csv')
            stats_df.to_csv(stats_file, index=False, encoding='utf-8-sig')
            
            # 记录日志
            logging.info(f"策略共振分析已保存到: {file_path}")
            self._log_confluence_summary(strategy_counts)
            
            return df
        return None
    
    def save_strategy_signals(self, stock_signals):
        """保存个股策略信号"""
        results = []
        for code, signals in stock_signals.items():
            stock_code, stock_name = code
            for strategy, signal in signals:
                results.append({
                    '日期': self.date_str,
                    '股票代码': stock_code,
                    '股票名称': stock_name,
                    '策略': strategy,
                    '信号': signal
                })
        
        if results:
            df = pd.DataFrame(results)
            file_path = os.path.join(self.results_dir, f'strategy_signals_{self.date_str}.csv')
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            logging.info(f"策略信号已保存到: {file_path}")
            return df
        return None
    
    def save_market_stats(self, stats_data):
        """保存市场统计数据"""
        file_path = os.path.join(self.results_dir, f'market_stats_{self.date_str}.csv')
        pd.DataFrame([stats_data]).to_csv(file_path, index=False, encoding='utf-8-sig')
        logging.info(f"市场统计数据已保存到: {file_path}")
    
    def generate_daily_report(self, stock_signals, market_stats):
        """生成每日策略报告"""
        report_data = {
            '日期': self.date_str,
            '市场统计': market_stats,
            '策略信号': self.save_strategy_signals(stock_signals),
            '策略共振': self.analyze_strategy_confluence(stock_signals)
        }
        
        # 生成HTML报告
        html_path = os.path.join(self.results_dir, f'daily_report_{self.date_str}.html')
        self._generate_html_report(report_data, html_path)
        logging.info(f"每日报告已生成: {html_path}")
    
    def _generate_html_report(self, report_data, html_path):
        """生成HTML格式的报告"""
        html_content = f"""
        <html>
        <head>
            <title>策略��析报告 - {self.date_str}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .section {{ margin-bottom: 30px; }}
                h2 {{ color: #333; }}
            </style>
        </head>
        <body>
            <h1>策略分析报告 - {self.date_str}</h1>
            
            <div class="section">
                <h2>市场概况</h2>
                {self._market_stats_to_html(report_data['市场统计'])}
            </div>
            
            <div class="section">
                <h2>策略共振分析</h2>
                {self._confluence_to_html(report_data['策略共振'])}
            </div>
            
            <div class="section">
                <h2>个股策略信号</h2>
                {self._signals_to_html(report_data['策略信号'])}
            </div>
        </body>
        </html>
        """
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _market_stats_to_html(self, stats):
        """将市场统计数据转换为HTML表格"""
        if not stats:
            return "<p>无市场统计数据</p>"
            
        html = "<table>"
        html += "<tr><th>指标</th><th>数值</th></tr>"
        for key, value in stats.items():
            html += f"<tr><td>{key}</td><td>{value}</td></tr>"
        html += "</table>"
        return html
    
    def _confluence_to_html(self, confluence_df):
        """将策略共振数据转换为HTML表格"""
        if confluence_df is None or confluence_df.empty:
            return "<p>无策略共振数据</p>"
            
        return confluence_df.to_html(index=False, classes='dataframe')
    
    def _signals_to_html(self, signals_df):
        """将策略信号数据转换为HTML表格"""
        if signals_df is None or signals_df.empty:
            return "<p>无策略信号数据</p>"
            
        return signals_df.to_html(index=False, classes='dataframe')
    
    def _log_confluence_summary(self, strategy_counts):
        """记录共振统计���"""
        logging.info("=== 策略共振统计 ===")
        for count, num_stocks in sorted(strategy_counts.items(), reverse=True):
            logging.info(f"触发{count}个策略的股票数量: {num_stocks}")
        logging.info("==================")
    
    def _market_stats_to_html(self, stats):
        """将市场统计数据转换为HTML格式"""
        if not stats:
            return "<p>无市场统计数据</p>"
            
        html = "<h2>市场统计</h2>"
        html += "<table border='1'>"
        html += "<tr><th>指标</th><th>数值</th></tr>"
        
        for key, value in stats.items():
            html += f"<tr><td>{key}</td><td>{value}</td></tr>"
            
        html += "</table>"
        return html
    
    def _confluence_to_html(self, confluence_df):
        """将策略共振数据转换为HTML格式"""
        if confluence_df is None or confluence_df.empty:
            return "<p>无策略共振数据</p>"
        
        html = "<h2>策略共振数据</h2>"
        html += "<table border='1'>"
        html += "<tr><th>日期</th><th>股票代码</th><th>股票名称</th><th>触发策略数</th><th>触发策略列表</th></tr>"
        
        for _, row in confluence_df.iterrows():
            html += f"<tr><td>{row['日期']}</td><td>{row['股票代码']}</td><td>{row['股票名称']}</td><td>{row['触发策略数']}</td><td>{row['触发策略列表']}</td></tr>"
        
        html += "</table>"
        return html
    
    def _signals_to_html(self, signals):
        """将策略信号转换为HTML格式"""
        if not signals:
            return "<p>无策略信号</p>"
            
        html = "<h2>策略信号</h2>"
        html += "<table border='1'>"
        html += "<tr><th>股票代码</th><th>股票名称</th><th>触发策略</th></tr>"
        
        for code, signal_list in signals.items():
            stock_code, stock_name = code
            strategies = [s[0] for s in signal_list if s[1] == "买入"]
            if strategies:
                html += f"<tr><td>{stock_code}</td><td>{stock_name}</td><td>{', '.join(strategies)}</td></tr>"
            
        html += "</table>"
        return html


def prepare():
    """
    Prepare the workflow
    """
    # 统一获取数据，不再区分日线和周线
    stocks = data_fetcher.fetch_stock_data()
    
    logging.info("************************ process start ***************************************")
    
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

    process(stocks, strategies)
    
    logging.info("************************ process   end ***************************************")

def process(stocks, strategies):
    analyzer = StrategyAnalyzer()
    stocks_data = data_fetcher.run(stocks)
    stock_signals = defaultdict(list)
    
    for strategy, strategy_func in strategies.items():
        results = check_strategy(stocks_data, strategy, strategy_func)
        for code, signal in results.items():
            stock_signals[code].append((strategy, signal))
        time.sleep(2)
    
    # 生成市场统计数据
    market_stats = get_market_stats(stocks_data)
    
    # 生成完整报告
    analyzer.generate_daily_report(stock_signals, market_stats)

def check_strategy(stocks_data, strategy, strategy_func):
    """检查单个策略的信号"""
    end = settings.config['end_date']
    results = {}
    
    for code, data in stocks_data.items():
        if end is not None and end < data.iloc[0].日期:
            logging.debug(f"{code[0]}在{end}时还未上市")
            continue
            
        try:
            signal = strategy_func(code[0], data, end_date=end)
            results[code] = "买入" if signal else "观望"
        except Exception as e:
            logging.error(f"策略{strategy}处理股票{code}时出错：{str(e)}")
            results[code] = "错误"
    
    return results

def get_market_stats(stocks_data):
    """获取市场统计数据"""
    stats = {
        '日期': datetime.now().strftime('%Y%m%d'),
        '涨停数量': 0,
        '跌停数量': 0,
        '涨幅大于5%数量': 0,
        '跌幅大于5%数量': 0,
        '总股票数量': len(stocks_data)
    }
    
    for data in stocks_data.values():
        if len(data) > 0:
            last_price = data['收盘'].iloc[-1]
            prev_price = data['收盘'].iloc[-2] if len(data) > 1 else last_price
            change_pct = (last_price - prev_price) / prev_price * 100
            
            if change_pct >= 9.5:
                stats['涨停数量'] += 1
            elif change_pct <= -9.5:
                stats['跌停数量'] += 1
            elif change_pct >= 5:
                stats['涨幅大于5%数量'] += 1
            elif change_pct <= -5:
                stats['跌幅大于5%数量'] += 1
    
    return stats

def statistics(all_data, stocks):
    limitup = len(all_data.loc[(all_data['涨跌幅'] >= 9.5)])
    limitdown = len(all_data.loc[(all_data['涨跌幅'] <= -9.5)])
    up5 = len(all_data.loc[(all_data['涨跌幅'] >= 5)])
    down5 = len(all_data.loc[(all_data['涨跌幅'] <= -5)])

    msg = "涨停数：{}   跌停数：{}\n涨幅大于5%数：{}  跌幅大于5%数：{}".format(
        limitup, limitdown, up5, down5)
    logging.info(msg)
    push.statistics(msg)


