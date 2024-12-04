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
import datetime
from collections import defaultdict


def prepare():
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
    }

    if datetime.datetime.now().weekday() == 0:
        strategies['均线多头'] = keep_increasing.check

    process(stocks, strategies)


    logging.info("************************ process   end ***************************************")

def process(stocks, strategies):
    stocks_data = data_fetcher.run(stocks)
    # 使用defaultdict来收集每个股票的所有策略信号
    stock_signals = defaultdict(list)
    
    for strategy, strategy_func in strategies.items():
        results = check_strategy(stocks_data, strategy, strategy_func)
        # 收集每个策略的信号
        for code, signal in results.items():
            stock_signals[code].append((strategy, signal))
        time.sleep(2)
    
    # 输出汇总结果
    output_summary(stock_signals)

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

def output_summary(stock_signals):
    """输出汇总的策略信号"""
    logging.info("========== 策略信号汇总 ==========")
    
    # 筛选出有买入信号的股票
    buy_signals = defaultdict(list)
    for code, signals in stock_signals.items():
        buy_strategies = [strategy for strategy, signal in signals if signal == "买入"]
        if buy_strategies:
            buy_signals[code] = buy_strategies
    
    # 输出买入信号
    if buy_signals:
        logging.info("--- 买入信号 ---")
        for code, strategies in buy_signals.items():
            logging.info(f"股票: {code[0]}-{code[1]}")
            logging.info(f"    触发策略: {', '.join(strategies)}")
    
    # 输出统计信息
    logging.info("--- 策略统计 ---")
    strategy_stats = defaultdict(int)
    for signals in stock_signals.values():
        for strategy, signal in signals:
            if signal == "买入":
                strategy_stats[strategy] += 1
    
    for strategy, count in strategy_stats.items():
        logging.info(f"{strategy}: {count}个买入信号")
    
    logging.info("================================")

def statistics(all_data, stocks):
    limitup = len(all_data.loc[(all_data['涨跌幅'] >= 9.5)])
    limitdown = len(all_data.loc[(all_data['涨跌幅'] <= -9.5)])
    up5 = len(all_data.loc[(all_data['涨跌幅'] >= 5)])
    down5 = len(all_data.loc[(all_data['涨跌幅'] <= -5)])

    msg = "涨停数：{}   跌停数：{}\n涨幅大于5%数：{}  跌幅大于5%数：{}".format(
        limitup, limitdown, up5, down5)
    logging.info(msg)
    push.statistics(msg)


