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
        logger.info("开始获取A股列表...")
        # 获取所有A股列表
        stock_info = ak.stock_info_a_code_name()
        total_stocks = len(stock_info)
        logger.info(f"获取到原始股票数量: {total_stocks}")
        
        # 过滤条件
        def is_valid_stock(code, name):
            try:
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
            except Exception as e:
                logger.error(f"处理股票 {code} 时出错: {str(e)}")
                return False
        
        # 应用过滤条件并记录统计信息
        filtered_stocks = []
        st_count = 0
        delisted_count = 0
        sci_tech_count = 0
        beijing_count = 0
        other_count = 0
        
        for _, row in stock_info.iterrows():
            try:
                code = str(row['code'])
                name = str(row['name'])
                
                if 'ST' in name.upper():
                    st_count += 1
                    continue
                if '退' in name:
                    delisted_count += 1
                    continue
                if code.startswith('688'):
                    sci_tech_count += 1
                    continue
                if code.startswith('8'):
                    beijing_count += 1
                    continue
                    
                if code.startswith(('000', '001', '002', '003', '300', '600', '601', '603', '605')):
                    filtered_stocks.append((code, name))
                else:
                    other_count += 1
                    
            except Exception as e:
                logger.error(f"处理股票数据时出错: {str(e)}")
                continue
        
        # 输出详细的过滤统计
        logger.info(f"""
股票列表过滤统计:
- 原始股票总数: {total_stocks}
- ST股票数量: {st_count}
- 退市股票数量: {delisted_count}
- 科创板股票数量: {sci_tech_count}
- 北交所股票数量: {beijing_count}
- 其他不符合条件股票数量: {other_count}
- 最终有效股票数量: {len(filtered_stocks)}
        """)
        
        return filtered_stocks
        
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