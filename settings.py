# -*- encoding: UTF-8 -*-
import yaml
import os
import akshare as ak
import pandas as pd

def get_valid_stocks():
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
        
        return valid_stocks['code'].tolist()
    except Exception as e:
        print(f"获取股票列表失败: {str(e)}")
        return []

def init():
    global config
    global top_list
    
    # 加载配置文件
    root_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(root_dir, 'config.yaml')
    with open(config_file, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    # 获取所有有效股票
    top_list = get_valid_stocks()
    print(f"获取到 {len(top_list)} 只有效股票")

def config():
    return config