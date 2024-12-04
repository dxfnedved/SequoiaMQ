# -*- encoding: UTF-8 -*-

import akshare as ak
import logging
import talib as tl
import time
import concurrent.futures
from functools import wraps
from requests.exceptions import RequestException
from urllib3.exceptions import MaxRetryError, NewConnectionError

def retry_on_network_error(retries=3, delay=2):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except (RequestException, MaxRetryError, NewConnectionError) as e:
                    if attempt == retries - 1:  # 最后一次尝试
                        logging.error(f"在{retries}次尝试后获取数据失败: {str(e)}")
                        return None
                    logging.warning(f"第{attempt + 1}次尝试失败，{delay}秒后重试: {str(e)}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@retry_on_network_error(retries=3, delay=2)
def fetch(code_name):
    stock = code_name[0]
    
    # 过滤科创板股票
    if stock.startswith('68'):
        logging.debug(f"跳过科创板股票：{stock}")
        return None
        
    try:
        data = ak.stock_zh_a_hist(symbol=stock, period="daily", start_date="20220101", adjust="qfq")

        if data is None or data.empty:
            logging.debug(f"股票：{stock} 没有数据，略过...")
            return None

        # 确保数据类型正确
        data = data.astype({
            '成交量': 'float64',
            '收盘': 'float64',
            '开盘': 'float64',
            '最高': 'float64',
            '最低': 'float64'
        })

        data['p_change'] = tl.ROC(data['收盘'].values, 1)
        
        # 添加技术指标
        data['MA5'] = tl.MA(data['收盘'].values, timeperiod=5)
        data['MA20'] = tl.MA(data['收盘'].values, timeperiod=20)
        data['VOL_MA5'] = tl.MA(data['成交量'].values, timeperiod=5)
        data['VOL_MA20'] = tl.MA(data['成交量'].values, timeperiod=20)
        
        # 添加股票名称列
        data['名称'] = code_name[1]

        return data
        
    except Exception as e:
        logging.error(f"获取股票{stock}数据时出错：{str(e)}")
        return None

def run(stocks):
    stocks_data = {}
    failed_stocks = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_stock = {executor.submit(fetch, stock): stock for stock in stocks}
        for future in concurrent.futures.as_completed(future_to_stock):
            stock = future_to_stock[future]
            try:
                data = future.result()
                if data is not None:
                    stocks_data[stock] = data
                else:
                    failed_stocks.append(stock)
            except Exception as exc:
                logging.error(f'{stock[1]}({stock[0]}) generated an exception: {exc}')
                failed_stocks.append(stock)

    # 重试失败的股票
    if failed_stocks:
        logging.info(f"开始重试获取失败的股票数据，共{len(failed_stocks)}只...")
        time.sleep(5)  # 等待一段时间后重试
        
        for stock in failed_stocks:
            try:
                data = fetch(stock)
                if data is not None:
                    stocks_data[stock] = data
            except Exception as exc:
                logging.error(f'重试获取{stock[1]}({stock[0]})数据失败: {exc}')

    return stocks_data
