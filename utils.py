# -*- coding: UTF-8 -*-
import datetime
import akshare as ak
import pandas as pd
from logger_manager import LoggerManager

logger = LoggerManager().get_logger("utils")

def is_weekday():
    """是否是工作日"""
    return datetime.datetime.today().weekday() < 5

def get_stock_list():
    """获取有效的A股列表（剔除ST、退市、科创板和北交所股票）"""
    try:
        # 获取所有A股列表
        stock_info = ak.stock_info_a_code_name()
        
        # 过滤条件
        def is_valid_stock(code, name):
            # 排除ST股票
            if 'ST' in name.upper():
                return False
            # 排除退市股票
            if '退' in name:
                return False
            # 排除科创板股票
            if code.startswith('688'):
                return False
            # 排除北交所股票
            if code.startswith('8'):
                return False
            # 只保留沪深主板、中小板、创业板
            return code.startswith(('000', '001', '002', '003', '300', '600', '601', '603', '605'))
        
        # 应用过滤条件
        valid_stocks = stock_info[
            stock_info.apply(lambda x: is_valid_stock(x['code'], x['name']), axis=1)
        ]
        
        # 转换为(code, name)元组列表
        stock_list = list(zip(valid_stocks['code'].tolist(), valid_stocks['name'].tolist()))
        logger.info(f"获取到 {len(stock_list)} 只有效股票")
        return stock_list
        
    except Exception as e:
        logger.error(f"获取股票列表失败: {str(e)}")
        return []

def format_code(code):
    """格式化股票代码（添加市场标识）"""
    if code.startswith(('000', '001', '002', '003', '300')):
        return f"0.{code}"  # 深市
    elif code.startswith(('600', '601', '603', '605')):
        return f"1.{code}"  # 沪市
    return code