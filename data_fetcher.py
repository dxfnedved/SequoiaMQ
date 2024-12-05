# -*- encoding: UTF-8 -*-

import akshare as ak
import logging
import talib as tl
import time
import concurrent.futures
from functools import wraps
from requests.exceptions import RequestException
from urllib3.exceptions import MaxRetryError, NewConnectionError
import sys
from tqdm import tqdm
import colorama
from colorama import Fore, Style
import random

# 初始化colorama
colorama.init()

# 配置重试参数
MAX_RETRIES = 5
MIN_DELAY = 3
MAX_DELAY = 10

def retry_on_network_error(retries=MAX_RETRIES, min_delay=MIN_DELAY, max_delay=MAX_DELAY):
    """增强的重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            stock_code = args[0][0] if args else "Unknown"
            stock_name = args[0][1] if args and len(args[0]) > 1 else ""
            
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except (RequestException, MaxRetryError, NewConnectionError) as e:
                    if attempt == retries - 1:  # 最后一次尝试
                        print(f"{Fore.RED}\r获取股票 {stock_code}-{stock_name} 数据失败（已重试{retries}次），跳过...{Style.RESET_ALL}", 
                              file=sys.stderr)
                        return None
                    
                    # 使用指数退���算法计算延迟时间
                    delay = min(max_delay, min_delay * (2 ** attempt)) + random.uniform(0, 1)
                    print(f"{Fore.YELLOW}\r正在重试股票 {stock_code}-{stock_name} 数据获取，第{attempt + 1}次"
                          f"（等待{delay:.1f}秒）...{Style.RESET_ALL}", 
                          end="", file=sys.stderr)
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@retry_on_network_error()
def fetch(code_name):
    stock = code_name[0]
    
    # 过滤科创板股票
    if stock.startswith('68'):
        return None
        
    try:
        # 使用带有超时设置的请求
        data = ak.stock_zh_a_hist(
            symbol=stock, 
            period="daily", 
            start_date="20240101", 
            adjust="qfq"
        )

        if data is None or data.empty:
            return None

        # 创建数据副本以避免链式赋值警告
        data = data.copy()

        # 确保数据类型正确
        data = data.astype({
            '成交量': 'float64',
            '收盘': 'float64',
            '开盘': 'float64',
            '最高': 'float64',
            '最低': 'float64'
        })

        # 计算涨跌幅
        data.loc[:, 'p_change'] = ((data['收盘'] - data['收盘'].shift(1)) / data['收盘'].shift(1) * 100).round(2)
        data.loc[data['p_change'].isna(), 'p_change'] = 0

        # 添加更多技术指标
        for period in [5, 10, 20]:
            data[f'MA{period}'] = tl.MA(data['收盘'].values, timeperiod=period)
            data[f'VOL_MA{period}'] = tl.MA(data['成交量'].values, timeperiod=period)
        
        # 添加股票名称列
        data['名称'] = code_name[1]

        return data
        
    except Exception as e:
        print(f"{Fore.RED}\r获取股票 {stock}-{code_name[1]} 数据出错: {str(e)}{Style.RESET_ALL}", 
              file=sys.stderr)
        return None

def run(stocks):
    stocks_data = {}
    failed_stocks = []
    total_stocks = len(stocks)
    
    print(f"\n{Fore.CYAN}开始获取{total_stocks}只股票数据...{Style.RESET_ALL}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:  # 减少并发数以降低网络压力
        futures = {executor.submit(fetch, stock): stock for stock in stocks}
        
        with tqdm(total=total_stocks, desc="获取数据进度", ncols=100, 
                 bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
            for future in concurrent.futures.as_completed(futures):
                stock = futures[future]
                try:
                    data = future.result()
                    if data is not None:
                        stocks_data[stock] = data
                    else:
                        failed_stocks.append(stock)
                except Exception:
                    failed_stocks.append(stock)
                pbar.update(1)

    # 重试失败的股票
    if failed_stocks:
        failed_count = len(failed_stocks)
        print(f"\n{Fore.YELLOW}开始重试{failed_count}只失败的股票...{Style.RESET_ALL}")
        time.sleep(5)  # 等待一段时间后重试
        
        with tqdm(total=failed_count, desc="重试进度", ncols=100,
                 bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
            for stock in failed_stocks[:]:  # 使用切片创建副本以避免在迭代时修改列表
                try:
                    data = fetch(stock)
                    if data is not None:
                        stocks_data[stock] = data
                        failed_stocks.remove(stock)  # 成功后从失败列表中移除
                except Exception:
                    pass
                pbar.update(1)

    success_count = len(stocks_data)
    print(f"\n{Fore.GREEN}数据获取完成：成功{success_count}只，"
          f"{Fore.RED}失败{len(failed_stocks)}只{Style.RESET_ALL}")
    
    if failed_stocks:
        print(f"\n{Fore.YELLOW}失败股票列表：{Style.RESET_ALL}")
        for stock in failed_stocks:
            print(f"{stock[0]}-{stock[1]}")
    
    return stocks_data

def fetch_daily_data():
    """获取日线数据"""
    all_data = ak.stock_zh_a_spot_em()
    stocks = list(zip(all_data['代码'].tolist(), all_data['名称'].tolist()))
    return run(stocks)

def fetch_weekly_data():
    """获取周线数据"""
    all_data = ak.stock_zh_a_spot_em()
    stocks = list(zip(all_data['代码'].tolist(), all_data['名称'].tolist()))
    return run(stocks)
