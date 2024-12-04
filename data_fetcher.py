# -*- encoding: UTF-8 -*-

import akshare as ak
import logging
import talib as tl

import concurrent.futures


def fetch(code_name):
    stock = code_name[0]
    
    # 过滤科创板股票
    if stock.startswith('68'):
        logging.debug(f"跳过科创板股票：{stock}")
        return None
        
    try:
        data = ak.stock_zh_a_hist(symbol=stock, period="daily", start_date="20220101", adjust="qfq")

        if data is None or data.empty:
            logging.debug("股票："+stock+" 没有数据，略过...")
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
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        future_to_stock = {executor.submit(fetch, stock): stock for stock in stocks}
        for future in concurrent.futures.as_completed(future_to_stock):
            stock = future_to_stock[future]
            try:
                data = future.result()
                if data is not None:
                    stocks_data[stock] = data
            except Exception as exc:
                logging.error('%s(%r) generated an exception: %s' % (stock[1], stock[0], exc))

    return stocks_data
