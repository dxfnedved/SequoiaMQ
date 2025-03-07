import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetcher import DataFetcher
from logger_manager import LoggerManager

class StockDataLoader:
    def __init__(self, logger_manager=None):
        """初始化数据加载器"""
        # 初始化日志管理器
        self.logger_manager = logger_manager if logger_manager is not None else LoggerManager()
        self.logger = self.logger_manager.get_logger("stock_data_loader")
        
        # 初始化数据获取器
        self.data_fetcher = DataFetcher(logger_manager=self.logger_manager)
        
        self.logger.info("StockDataLoader初始化完成")
    
    def get_stock_data(self, stock_code, start_date=None, end_date=None):
        """
        获取股票历史数据并进行LSTM预处理
        
        参数:
            stock_code (str): 股票代码（如：'000001'为平安银行）
            start_date (str): 开始日期，格式：'YYYYMMDD'
            end_date (str): 结束日期，格式：'YYYYMMDD'
            
        返回:
            pd.DataFrame: 包含处理后的股票数据，主要用于LSTM模型训练
        """
        try:
            # 如果未指定日期，默认获取近五年数据（从3年改为5年，提高模型预测准确性和稳定性）
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=1825)).strftime('%Y%m%d')
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
            
            # 确保股票代码格式正确
            formatted_code = self.format_stock_code(stock_code)
            self.logger.info(f"正在获取股票数据: {formatted_code}, 时间范围: {start_date} 到 {end_date}")
            
            # 直接使用akshare获取A股历史数据
            df = ak.stock_zh_a_hist(symbol=formatted_code, 
                                  period="daily",
                                  start_date=start_date,
                                  end_date=end_date,
                                  adjust="qfq")  # 前复权数据
            
            if df is None or df.empty:
                self.logger.error(f"获取股票 {formatted_code} 数据为空")
                return None
            
            # 标准化列名
            column_map = {
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'pct_change',
                '涨跌额': 'change',
                '换手率': 'turnover'
            }
            
            # 重命名存在的列
            rename_dict = {k: v for k, v in column_map.items() if k in df.columns}
            if rename_dict:
                df = df.rename(columns=rename_dict)
            
            # 设置日期索引
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
            
            # 只保留需要的列
            if 'close' in df.columns:
                df = df[['close']]
            else:
                self.logger.error(f"股票 {formatted_code} 数据缺少收盘价列")
                return None
            
            # 确保数据按日期排序
            df.sort_index(inplace=True)
            
            # 添加LSTM特定的特征
            df = self._add_lstm_features(df)
            
            self.logger.info(f"成功获取股票 {formatted_code} 数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            self.logger.error(f"获取股票数据时出错: {str(e)}")
            return None
    
    def _add_lstm_features(self, df):
        """添加LSTM模型需要的特征"""
        try:
            # 计算移动平均线
            df['ma5'] = df['close'].rolling(window=5).mean()
            df['ma10'] = df['close'].rolling(window=10).mean()
            df['ma20'] = df['close'].rolling(window=20).mean()
            
            # 计算价格变化率
            df['price_change'] = df['close'].pct_change()
            
            # 计算波动率（20日标准差）
            df['volatility'] = df['price_change'].rolling(window=20).std()
            
            # 移除NaN值
            df.dropna(inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"添加LSTM特征时出错: {str(e)}")
            return None
    
    def get_stock_name(self, stock_code):
        """获取股票名称"""
        try:
            # 尝试从akshare获取股票名称
            df = ak.stock_zh_a_spot_em()
            stock_info = df[df['代码'] == stock_code]
            if not stock_info.empty:
                name = stock_info.iloc[0]['名称']
                self.logger.info(f"找到股票: {stock_code} - {name}")
                return name
            
            self.logger.warning(f"未找到股票: {stock_code}")
            return stock_code
        except Exception as e:
            self.logger.error(f"获取股票名称时出错: {str(e)}")
            return stock_code
    
    def validate_stock_code(self, stock_code):
        """验证股票代码是否有效"""
        try:
            # 简单验证：只要是6位数字就认为是有效的
            if stock_code.isdigit() and len(stock_code) == 6:
                self.logger.info(f"股票代码 {stock_code} 有效")
                return True
                
            # 如果不是6位数字，尝试通过akshare验证
            try:
                df = ak.stock_zh_a_spot_em()
                is_valid = stock_code in df['代码'].values
                
                if is_valid:
                    self.logger.info(f"股票代码 {stock_code} 有效")
                    return True
            except:
                self.logger.warning(f"通过akshare验证股票代码失败，将尝试直接使用")
            
            # 如果以上验证都失败，但代码看起来像股票代码，也认为是有效的
            if stock_code.isdigit() and len(stock_code) >= 4:
                self.logger.warning(f"股票代码 {stock_code} 格式不标准，但将尝试使用")
                return True
                
            self.logger.warning(f"股票代码 {stock_code} 无效")
            return False
        except Exception as e:
            self.logger.error(f"验证股票代码时出错: {str(e)}")
            # 出错时也尝试使用
            return True
    
    def format_stock_code(self, code):
        """格式化股票代码"""
        try:
            # 确保股票代码是6位数字
            code = str(code).strip().upper()
            
            # 移除可能的前缀
            prefixes = ['SH', 'SZ', 'BJ', 'SH.', 'SZ.', 'BJ.']
            for prefix in prefixes:
                if code.startswith(prefix):
                    code = code[len(prefix):]
                    break
            
            # 确保是6位数字
            if code.isdigit():
                code = code.zfill(6)
                
            self.logger.info(f"格式化股票代码: {code}")
            return code
        except Exception as e:
            self.logger.error(f"格式化股票代码时出错: {str(e)}")
            return str(code) 