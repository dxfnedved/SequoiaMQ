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


def ensure_dir_exists(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)


class ResultManager:
    def __init__(self, base_dir="results"):
        self.base_dir = base_dir
        self.date_str = datetime.now().strftime('%Y%m%d')
        self.time_str = datetime.now().strftime('%H%M%S')
        
        # 创建日期目录
        self.date_dir = os.path.join(base_dir, self.date_str)
        ensure_dir_exists(self.date_dir)
        
        # 创建本次执行的时间目录
        self.result_dir = os.path.join(self.date_dir, self.time_str)
        ensure_dir_exists(self.result_dir)
        
        # 设置日志
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志系统"""
        # 创建日志目录
        log_base = "logs"
        ensure_dir_exists(log_base)
        log_date_dir = os.path.join(log_base, self.date_str)
        ensure_dir_exists(log_date_dir)
        log_time_dir = os.path.join(log_date_dir, self.time_str)
        ensure_dir_exists(log_time_dir)
        
        # 设置日志文件
        log_file = os.path.join(log_time_dir, "execution.log")
        
        # 配置根日志记录器
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()  # 同时输出到控制台
            ]
        )
        
        # 配置策略专用日志记录器
        strategy_logger = logging.getLogger('RARA_Strategy')
        strategy_logger.setLevel(logging.DEBUG)
        strategy_log_file = os.path.join(log_time_dir, "strategy_RARA.log")
        fh = logging.FileHandler(strategy_log_file, encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        strategy_logger.addHandler(fh)
        
        # 配置Alpha策略日志记录器
        alpha_logger = logging.getLogger('Alpha_Strategy')
        alpha_logger.setLevel(logging.INFO)
        alpha_log_file = os.path.join(log_time_dir, "strategy_alpha.log")
        fh = logging.FileHandler(alpha_log_file, encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        alpha_logger.addHandler(fh)
    
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
            file_path = os.path.join(self.result_dir, 'strategy_signals.csv')
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            logging.info(f"策略信号已保存到: {file_path}")
            return df
        return None
    
    def save_market_stats(self, stats_data):
        """保存市场统计数据"""
        file_path = os.path.join(self.result_dir, 'market_stats.csv')
        pd.DataFrame([stats_data]).to_csv(file_path, index=False, encoding='utf-8-sig')
        logging.info(f"市场统计数据已保存到: {file_path}")
    
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
            file_path = os.path.join(self.result_dir, 'strategy_confluence.csv')
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            # 保存共振统计信息
            stats_data = {
                '日期': [self.date_str] * len(strategy_counts),
                '触发策略数': list(strategy_counts.keys()),
                '股票数量': list(strategy_counts.values())
            }
            stats_df = pd.DataFrame(stats_data)
            stats_file = os.path.join(self.result_dir, 'confluence_statistics.csv')
            stats_df.to_csv(stats_file, index=False, encoding='utf-8-sig')
            
            # 记录日志
            logging.info(f"策略共振分析已保存到: {file_path}")
            self._log_confluence_summary(strategy_counts)
            
            return df
        return None
    
    def _log_confluence_summary(self, strategy_counts):
        """记录共振统计摘要"""
        logging.info("=== 策略共振统计 ===")
        for count, num_stocks in sorted(strategy_counts.items(), reverse=True):
            logging.info(f"触发{count}个策略的股票数量: {num_stocks}")
        logging.info("==================")


def prepare():
    """
    Prepare the workflow
    """
    if datetime.now().weekday() == 0:
        # Monday, fetch weekly data
        stocks = data_fetcher.fetch_weekly_data()
    else:
        # Other days, fetch daily data
        stocks = data_fetcher.fetch_daily_data()
    
    logging.info("************************ process start ***************************************")
    all_data = ak.stock_zh_a_spot_em()
    
    # 过滤科创板股票
    all_data = all_data[~all_data['代码'].str.startswith('68')]
    
    subset = all_data[['代码', '名称']]
    stocks = [tuple(x) for x in subset.values]
    statistics(all_data, stocks)

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
        'Alpha101策略': alpha_factors101.check,
        'Alpha191策略': alpha_factors191.check,
    }

    if datetime.now().weekday() == 0:
        strategies['均线多头'] = keep_increasing.check

    process(stocks, strategies)

    logging.info("************************ process   end ***************************************")


def process(stocks, strategies):
    result_mgr = ResultManager()
    stocks_data = data_fetcher.run(stocks)
    stock_signals = defaultdict(list)
    
    for strategy, strategy_func in strategies.items():
        results = check_strategy(stocks_data, strategy, strategy_func)
        for code, signal in results.items():
            stock_signals[code].append((strategy, signal))
        time.sleep(2)
    
    # 生成市场统计数据
    market_stats = get_market_stats(stocks_data)
    
    # 保存分析结果
    result_mgr.save_market_stats(market_stats)
    result_mgr.save_strategy_signals(stock_signals)
    result_mgr.analyze_strategy_confluence(stock_signals)


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


