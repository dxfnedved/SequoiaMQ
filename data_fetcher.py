# -*- encoding: UTF-8 -*-

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from logger_manager import LoggerManager

class DataFetcher:
    """数据获取类"""
    def __init__(self, logger_manager=None):
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("data_fetcher")
        
    def get_stock_list(self):
        """获取A股列表"""
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
            
            self.logger.info(f"获取到 {len(valid_stocks)} 只有效股票")
            return valid_stocks.to_dict('records')
            
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {str(e)}")
            return []
            
    def get_stock_data(self, code):
        """获取股票历史数据"""
        try:
            print(f"正在获取股票 {code} 的历史数据...")
            # 获取最近一年的日线数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            # 格式化日期
            start_date_str = start_date.strftime('%Y%m%d')
            end_date_str = end_date.strftime('%Y%m%d')
            
            # 使用akshare获取数据
            df = ak.stock_zh_a_hist(symbol=code, start_date=start_date_str, end_date=end_date_str)
            
            # 重命名列
            df = df.rename(columns={
                '日期': 'date',
                '开盘': '开盘',
                '收盘': '收盘',
                '最高': '最高',
                '最低': '最低',
                '成交量': '成交量',
                '成交额': '成交额',
                '振幅': '振幅',
                '涨跌幅': 'p_change',
                '涨跌额': '涨跌额',
                '换手率': '换手率'
            })
            
            # 设置日期索引
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            print(f"成功获取股票 {code} 的历史数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            error_msg = f"获取股票 {code} 数据失败: {str(e)}"
            print(error_msg)
            self.logger.error(error_msg)
            return None
