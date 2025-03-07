import akshare as ak
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from loguru import logger
import traceback
import json
import talib
from logger_manager import LoggerManager

class TechnicalAnalyzer:
    """技术分析器，用于计算各种技术指标"""
    
    def __init__(self):
        """初始化技术分析器"""
        self.logger = LoggerManager().get_logger("technical_analyzer")
        
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标
        
        Args:
            df (pd.DataFrame): 包含OHLCV数据的DataFrame
            
        Returns:
            pd.DataFrame: 添加了技术指标的DataFrame
        """
        try:
            # 确保数据格式正确
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_columns):
                self.logger.error("数据缺少必要的OHLCV列")
                return df
            
            # 移动平均线
            self._add_moving_averages(df)
            
            # MACD指标
            self._add_macd(df)
            
            # RSI指标
            self._add_rsi(df)
            
            # 布林带
            self._add_bollinger_bands(df)
            
            # 成交量指标
            self._add_volume_indicators(df)
            
            # KDJ指标
            self._add_kdj(df)
            
            # BOLL通道宽度
            self._add_boll_width(df)
            
            # 趋势强度指标
            self._add_trend_strength(df)
            
            # 波动率指标
            self._add_volatility(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"计算技术指标时出错: {str(e)}")
            return df
    
    def _add_moving_averages(self, df: pd.DataFrame) -> None:
        """添加移动平均线指标"""
        try:
            periods = [5, 10, 20, 30, 60]
            for period in periods:
                df[f'MA{period}'] = talib.MA(df['close'], timeperiod=period)
                df[f'EMA{period}'] = talib.EMA(df['close'], timeperiod=period)
        except Exception as e:
            self.logger.error(f"计算移动平均线时出错: {str(e)}")
    
    def _add_macd(self, df: pd.DataFrame) -> None:
        """添加MACD指标"""
        try:
            df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = talib.MACD(
                df['close'],
                fastperiod=12,
                slowperiod=26,
                signalperiod=9
            )
        except Exception as e:
            self.logger.error(f"计算MACD时出错: {str(e)}")
    
    def _add_rsi(self, df: pd.DataFrame) -> None:
        """添加RSI指标"""
        try:
            periods = [6, 12, 24]
            for period in periods:
                df[f'RSI{period}'] = talib.RSI(df['close'], timeperiod=period)
        except Exception as e:
            self.logger.error(f"计算RSI时出错: {str(e)}")
    
    def _add_bollinger_bands(self, df: pd.DataFrame) -> None:
        """添加布林带指标"""
        try:
            df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = talib.BBANDS(
                df['close'],
                timeperiod=20,
                nbdevup=2,
                nbdevdn=2,
                matype=0
            )
        except Exception as e:
            self.logger.error(f"计算布林带时出错: {str(e)}")
    
    def _add_volume_indicators(self, df: pd.DataFrame) -> None:
        """添加成交量相关指标"""
        try:
            # 成交量移动平均
            df['Volume_MA5'] = talib.MA(df['volume'], timeperiod=5)
            df['Volume_MA10'] = talib.MA(df['volume'], timeperiod=10)
            
            # 成交量比率
            df['Volume_Ratio'] = df['volume'] / df['Volume_MA5']
            
            # 资金流向指标(MFI)
            df['MFI'] = talib.MFI(df['high'], df['low'], df['close'], df['volume'], timeperiod=14)
            
            # 能量潮指标(OBV)
            df['OBV'] = talib.OBV(df['close'], df['volume'])
        except Exception as e:
            self.logger.error(f"计算成交量指标时出错: {str(e)}")
    
    def _add_kdj(self, df: pd.DataFrame) -> None:
        """添加KDJ指标"""
        try:
            # 计算KDJ
            df['K'], df['D'] = talib.STOCH(df['high'], 
                                         df['low'], 
                                         df['close'],
                                         fastk_period=9,
                                         slowk_period=3,
                                         slowk_matype=0,
                                         slowd_period=3,
                                         slowd_matype=0)
            df['J'] = 3 * df['K'] - 2 * df['D']
        except Exception as e:
            self.logger.error(f"计算KDJ时出错: {str(e)}")
    
    def _add_boll_width(self, df: pd.DataFrame) -> None:
        """添加布林带宽度"""
        try:
            df['BOLL_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        except Exception as e:
            self.logger.error(f"计算布林带宽度时出错: {str(e)}")
    
    def _add_trend_strength(self, df: pd.DataFrame) -> None:
        """添加趋势强度指标"""
        try:
            # ADX - 趋势强度指标
            df['ADX'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
            
            # DMI指标
            df['PLUS_DI'] = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
            df['MINUS_DI'] = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
        except Exception as e:
            self.logger.error(f"计算趋势强度指标时出错: {str(e)}")
    
    def _add_volatility(self, df: pd.DataFrame) -> None:
        """添加波动率指标"""
        try:
            # ATR - 真实波幅
            df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            
            # 计算历史波动率
            df['Daily_Return'] = df['close'].pct_change()
            df['Volatility'] = df['Daily_Return'].rolling(window=20).std() * np.sqrt(252)
        except Exception as e:
            self.logger.error(f"计算波动率指标时出错: {str(e)}")
    
    def get_latest_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取最新的交易信号
        
        Args:
            df (pd.DataFrame): 包含技术指标的DataFrame
            
        Returns:
            Dict[str, Any]: 包含各种交易信号的字典
        """
        try:
            latest = df.iloc[-1]
            signals = {
                'MACD': {
                    'signal': 'buy' if latest['MACD'] > latest['MACD_Signal'] else 'sell',
                    'strength': abs(latest['MACD'] - latest['MACD_Signal'])
                },
                'RSI': {
                    'signal': 'buy' if latest['RSI14'] < 30 else 'sell' if latest['RSI14'] > 70 else 'neutral',
                    'value': latest['RSI14']
                },
                'Bollinger': {
                    'signal': 'buy' if latest['close'] < latest['BB_Lower'] else 'sell' if latest['close'] > latest['BB_Upper'] else 'neutral',
                    'width': latest['BOLL_Width']
                },
                'Volume': {
                    'signal': 'buy' if latest['Volume_Ratio'] > 2.0 else 'sell' if latest['Volume_Ratio'] < 0.5 else 'neutral',
                    'ratio': latest['Volume_Ratio']
                },
                'Trend': {
                    'signal': 'buy' if latest['PLUS_DI'] > latest['MINUS_DI'] else 'sell',
                    'strength': latest['ADX']
                }
            }
            return signals
        except Exception as e:
            self.logger.error(f"获取交易信号时出错: {str(e)}")
            return {}
            
    def get_technical_indicators(self, code_or_name: str) -> dict:
        """获取技术指标
        
        Args:
            code_or_name: 股票代码或名称
        Returns:
            包含各类技术指标的字典
        """
        try:
            # 获取股票数据
            df = self._get_stock_data(code_or_name)
            if df.empty:
                self.logger.warning(f"未获取到股票数据: {code_or_name}")
                return {}
                
            # 初始化指标字典
            indicators = {}
            
            # 计算MA
            ma_data = self._calculate_ma(df)
            if ma_data:
                # 确保所有值都是Python原生float类型
                indicators['MA'] = {k: float(v) for k, v in ma_data.items()}
            
            # 计算MACD
            macd_data = self._calculate_macd(df)
            if macd_data:
                # 确保所有值都是Python原生float类型
                indicators['MACD'] = {k: float(v) for k, v in macd_data.items()}
            
            # 计算RSI
            rsi_value = self._calculate_rsi(df)
            if rsi_value is not None:
                # 确保值是Python原生float类型
                indicators['RSI'] = float(rsi_value)
            
            # 计算布林带
            boll_data = self._calculate_bollinger_bands(df)
            if boll_data:
                # 确保所有值都是Python原生float类型
                indicators['BOLL'] = {k: float(v) for k, v in boll_data.items()}
            
            # 计算成交量指标
            volume_data = self._calculate_volume_indicators(df)
            if volume_data:
                # 对于成交量指标，保持字符串格式的数据不变，只转换数值类型
                indicators['VOLUME'] = {
                    k: (float(v) if isinstance(v, (int, float, np.integer, np.floating)) else v)
                    for k, v in volume_data.items()
                }
            
            # 获取价格信息
            price_data = self._get_price_info(df)
            if price_data:
                # 确保所有值都是Python原生float类型
                indicators['PRICE'] = {k: float(v) for k, v in price_data.items()}
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"计算技术指标时发生错误: {str(e)}")
            self.logger.debug(f"详细错误信息: {e}", exc_info=True)
            return {}
            
    def _get_pure_stock_code(self, code_or_name: str) -> str:
        """获取纯净的股票代码（不带市场前缀）
        
        Args:
            code_or_name: 股票代码或名称
        Returns:
            str: 纯净的股票代码
        """
        try:
            print(f"尝试获取股票代码: {code_or_name}")
            
            # 如果输入的是带市场前缀的代码，去除前缀
            if isinstance(code_or_name, str):
                pure_code = code_or_name.replace('sh', '').replace('sz', '')
                
                # 如果是6位数字，直接返回
                if pure_code.isdigit() and len(pure_code) == 6:
                    print(f"输入是6位数字代码: {pure_code}")
                    return pure_code
                    
                # 如果输入的是股票名称，获取股票代码
                try:
                    import akshare as ak
                    print(f"尝试通过akshare获取股票代码列表...")
                    stock_list = ak.stock_info_a_code_name()
                    print(f"成功获取股票代码列表，共 {len(stock_list)} 条记录")
                    
                    # 尝试精确匹配
                    matched = stock_list[stock_list['name'] == code_or_name]
                    if not matched.empty:
                        code = matched.iloc[0]['code']
                        print(f"找到精确匹配的股票代码: {code}")
                        return code
                        
                    # 尝试模糊匹配
                    matched = stock_list[stock_list['name'].str.contains(code_or_name)]
                    if not matched.empty:
                        code = matched.iloc[0]['code']
                        print(f"找到模糊匹配的股票代码: {code}")
                        return code
                        
                    print(f"未找到匹配的股票: {code_or_name}")
                    
                    # 如果是常见股票，直接返回代码
                    common_stocks = {
                        "平安银行": "000001",
                        "贵州茅台": "600519",
                        "中国平安": "601318",
                        "招商银行": "600036",
                        "格力电器": "000651",
                        "五粮液": "000858",
                        "恒瑞医药": "600276",
                        "茅台": "600519",
                        "腾讯": "00700",
                        "阿里巴巴": "09988"
                    }
                    
                    if code_or_name in common_stocks:
                        code = common_stocks[code_or_name]
                        print(f"使用常见股票映射: {code_or_name} -> {code}")
                        return code
                    
                except Exception as e:
                    print(f"通过akshare获取股票代码失败: {str(e)}")
                    
                    # 如果是常见股票，直接返回代码
                    common_stocks = {
                        "平安银行": "000001",
                        "贵州茅台": "600519",
                        "中国平安": "601318",
                        "招商银行": "600036",
                        "格力电器": "000651",
                        "五粮液": "000858",
                        "恒瑞医药": "600276",
                        "茅台": "600519",
                        "腾讯": "00700",
                        "阿里巴巴": "09988"
                    }
                    
                    if code_or_name in common_stocks:
                        code = common_stocks[code_or_name]
                        print(f"使用常见股票映射: {code_or_name} -> {code}")
                        return code
            
            # 如果是数字，尝试格式化为6位代码
            if isinstance(code_or_name, (int, float)) or (isinstance(code_or_name, str) and code_or_name.isdigit()):
                code = str(code_or_name).zfill(6)
                print(f"格式化为6位代码: {code}")
                return code
                
            print(f"无法解析股票代码或名称: {code_or_name}")
            return ""
            
        except Exception as e:
            print(f"获取股票代码失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return ""
            
    def _get_stock_data(self, code_or_name: str) -> pd.DataFrame:
        """获取股票数据"""
        try:
            # 获取纯净的股票代码
            pure_code = self._get_pure_stock_code(code_or_name)
            if not pure_code:
                self.logger.error(f"无法获取有效的股票代码: {code_or_name}")
                return pd.DataFrame()
                
            # 获取当前日期和时间
            now = pd.Timestamp.now()
            current_date = now.strftime('%Y-%m-%d')
            current_time = now.strftime('%H:%M:%S')
            
            # 判断是否是交易时间
            is_trading_time = (
                now.weekday() < 5 and  # 周一到周五
                ((now.hour == 9 and now.minute >= 30) or  # 9:30-11:30
                 (now.hour == 10) or
                 (now.hour == 11 and now.minute <= 30) or
                 (now.hour >= 13 and now.hour < 15))  # 13:00-15:00
            )
            
            self.logger.info(f"当前时间: {current_date} {current_time}")
            self.logger.info(f"是否在交易时间: {is_trading_time}")
            
            # 获取60天前的日期作为起始日期
            start_date = (now - pd.Timedelta(days=60)).strftime('%Y-%m-%d')
            
            self.logger.info(f"开始获取股票数据: {pure_code}")
            self.logger.info(f"查询日期范围: {start_date} 到 {current_date}")
            
            # 获取历史数据
            df = self._get_historical_data(pure_code, start_date, current_date)
            if df.empty:
                return df
            
            # 如果是交易时间，尝试获取实时数据
            if is_trading_time:
                try:
                    self.logger.debug("尝试获取实时数据")
                    # 使用 stock_zh_a_spot_em 获取实时行情
                    realtime_data = ak.stock_zh_a_spot_em()
                    
                    # 过滤出目标股票的实时数据
                    realtime_stock = realtime_data[realtime_data['代码'] == pure_code]
                    if not realtime_stock.empty:
                        self.logger.info("获取到实时数据")
                        self.logger.debug(f"实时数据:\n{realtime_stock.to_string()}")
                        
                        # 创建实时数据行
                        realtime_row = pd.DataFrame({
                            '日期': [pd.Timestamp(current_date)],
                            '开盘': [float(realtime_stock['开盘'].iloc[0])],
                            '最高': [float(realtime_stock['最高'].iloc[0])],
                            '最低': [float(realtime_stock['最低'].iloc[0])],
                            '收盘': [float(realtime_stock['最新价'].iloc[0])],
                            '成交量': [float(realtime_stock['成交量'].iloc[0])],
                            '成交额': [float(realtime_stock['成交额'].iloc[0])],
                            '换手率': [float(realtime_stock['换手率'].iloc[0])]
                        })
                        
                        # 设置日期为索引
                        realtime_row.set_index('日期', inplace=True)
                        
                        # 检查是否已经存在当天数据，如果存在则更新，不存在则添加
                        if current_date in df.index:
                            df.loc[current_date] = realtime_row.iloc[0]
                        else:
                            df = pd.concat([realtime_row, df])
                            
                        self.logger.info("实时数据已合并到历史数据中")
                        self.logger.debug(f"合并后最新数据:\n{df.head().to_string()}")
                    else:
                        self.logger.warning(f"未找到股票 {pure_code} 的实时数据")
                        
                except Exception as e:
                    self.logger.warning(f"获取实时数据失败: {str(e)}")
                    self.logger.debug(f"错误详情:\n{traceback.format_exc()}")
            
            # 计算其他指标
            df['振幅'] = ((df['最高'] - df['最低']) / df['开盘'] * 100).round(2)
            df['涨跌幅'] = ((df['收盘'] - df['收盘'].shift(1)) / df['收盘'].shift(1) * 100).round(2)
            df['涨跌额'] = (df['收盘'] - df['收盘'].shift(1)).round(2)
            
            # 按日期排序（确保降序排列，最新数据在前）
            df = df.sort_index(ascending=False)
            
            self.logger.info(f"处理后数据信息:")
            self.logger.info(f"- 数据条数: {len(df)}")
            self.logger.info(f"- 日期范围: {df.index.min()} 到 {df.index.max()}")
            self.logger.info(f"- 最新收盘价: {df['收盘'].iloc[0]}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取股票数据失败: {str(e)}")
            self.logger.debug(f"错误详情:\n{traceback.format_exc()}")
            return pd.DataFrame()
            
    def _get_historical_data(self, pure_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取历史数据
        
        Args:
            pure_code: 股票代码（不带市场标识）
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            
        Returns:
            DataFrame: 包含历史数据的DataFrame
        """
        try:
            # 判断股票市场
            market = 'sh' if pure_code.startswith('6') else 'sz'
            is_cyb = pure_code.startswith('300') or pure_code.startswith('301')  # 创业板
            is_kc = pure_code.startswith('688') or pure_code.startswith('689')   # 科创板
            
            self.logger.info(f"股票市场: {'创业板' if is_cyb else '科创板' if is_kc else '主板'}")
            
            # 尝试使用东方财富数据接口
            try:
                self.logger.debug(f"尝试使用东方财富数据接口获取数据, code={pure_code}")
                
                # 使用东方财富的stock_zh_a_hist接口
                df = ak.stock_zh_a_hist(
                    symbol=pure_code,
                    period="daily",
                    start_date=start_date.replace('-', ''),  # 修改日期格式
                    end_date=end_date.replace('-', ''),      # 修改日期格式
                    adjust="qfq"  # 前复权
                )
                
                # 验证返回的数据
                if df is None or df.empty:
                    self.logger.warning("东方财富接口返回空数据，尝试备用数据源")
                    raise ValueError("数据源返回空数据")
                
                self.logger.info(f"东方财富数据获取成功，数据条数: {len(df)}")
                
            except Exception as e1:
                self.logger.warning(f"使用东方财富数据接口失败: {str(e1)}")
                
                # 备用方案：使用东方财富网另一个接口
                try:
                    self.logger.debug(f"尝试使用东方财富备用接口获取数据, code={pure_code}")
                    
                    # 使用东方财富网另一个接口
                    df = ak.stock_zh_a_hist_min_em(
                        symbol=pure_code,
                        start_date=start_date.replace('-', ''),
                        end_date=end_date.replace('-', ''),
                        period='daily',
                        adjust='qfq'
                    )
                    
                    if df is None or df.empty:
                        self.logger.warning("东方财富备用接口返回空数据，尝试新浪财经接口")
                        # 尝试使用新浪财经的数据接口
                        symbol = f"{market}{pure_code}"
                        df = ak.stock_zh_a_daily(
                            symbol=symbol,
                            start_date=start_date.replace('-', ''),
                            end_date=end_date.replace('-', ''),
                            adjust="qfq"
                        )
                    
                    if df is None or df.empty:
                        self.logger.error("所有数据源都返回空数据")
                        return pd.DataFrame()
                    
                    self.logger.info(f"备用数据源获取成功，数据条数: {len(df)}")
                    
                except Exception as e2:
                    self.logger.error(f"所有数据源都失败:\n1. {str(e1)}\n2. {str(e2)}")
                    return pd.DataFrame()
            
            # 记录原始数据信息
            self.logger.debug(f"原始数据列: {df.columns.tolist()}")
            self.logger.debug(f"原始数据示例:\n{df.head().to_string()}")
            
            # 标准化列名
            rename_dict = {
                'date': '日期',
                'open': '开盘',
                'close': '收盘',
                'high': '最高',
                'low': '最低',
                'volume': '成交量',
                'amount': '成交额',
                'trade_date': '日期',
                '日期': '日期',
                '开盘': '开盘',
                '收盘': '收盘',
                '最高': '最高',
                '最低': '最低',
                '成交量': '成交量',
                '成交额': '成交额',
                '换手率': '换手率',
                '成交笔数': '成交笔数',
                'turnover': '换手率',
                '时间': '日期',
                '昨收': '昨收',
                '最新价': '收盘'
            }
            df = df.rename(columns=lambda x: rename_dict.get(x, x))
            
            # 确保必要的列存在
            required_columns = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"数据缺少必要的列: {missing_columns}")
                return pd.DataFrame()
            
            # 将日期列转换为datetime类型并设置为索引
            df['日期'] = pd.to_datetime(df['日期'])
            df.set_index('日期', inplace=True)
            
            # 确保数值列的类型正确
            numeric_columns = ['开盘', '收盘', '最高', '最低', '成交量', '成交额']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取历史数据失败: {str(e)}")
            self.logger.debug(f"错误详情:\n{traceback.format_exc()}")
            return pd.DataFrame()
            
    def _calculate_ma(self, df: pd.DataFrame) -> Dict[str, float]:
        """计算移动平均线"""
        try:
            ma_periods = [5, 10, 20]
            ma_dict = {}
            
            # 记录计算MA的数据信息
            self.logger.debug(f"计算MA使用的数据范围:")
            self.logger.debug(f"数据条数: {len(df)}")
            self.logger.debug(f"最新5条收盘价:\n{df['收盘'].head().to_string()}")
            
            # 将数据按日期升序排列用于计算
            df_asc = df.sort_index(ascending=True)
            self.logger.debug(f"排序后最新5条收盘价:\n{df_asc['收盘'].tail().to_string()}")
            
            for period in ma_periods:
                ma = df_asc['收盘'].rolling(window=period).mean()
                ma_value = float(ma.iloc[-1])  # 使用最后一条记录（最新数据）
                ma_dict[f'MA{period}'] = ma_value
                self.logger.debug(f"MA{period} 计算结果: {ma_value}")
                
            return ma_dict
            
        except Exception as e:
            self.logger.error(f"计算MA失败: {str(e)}")
            return {}
            
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        """计算RSI"""
        try:
            # 记录计算RSI的数据信息
            self.logger.debug(f"计算RSI使用的数据范围:")
            self.logger.debug(f"数据条数: {len(df)}")
            self.logger.debug(f"最新5条收盘价:\n{df['收盘'].head().to_string()}")
            
            # 将数据按日期升序排列用于计算
            df_asc = df.sort_index(ascending=True)
            self.logger.debug(f"排序后最新5条收盘价:\n{df_asc['收盘'].tail().to_string()}")
            
            delta = df_asc['收盘'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # 使用最后一条记录（最新数据）
            result = float(rsi.iloc[-1])
            self.logger.debug(f"RSI计算结果: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"计算RSI失败: {str(e)}")
            return 50.0
            
    def _calculate_macd(self, df: pd.DataFrame) -> Dict[str, float]:
        """计算MACD"""
        try:
            # 记录计算MACD的数据信息
            self.logger.debug(f"计算MACD使用的数据范围:")
            self.logger.debug(f"数据条数: {len(df)}")
            self.logger.debug(f"最新5条收盘价:\n{df['收盘'].head().to_string()}")
            
            # 将数据按日期升序排列用于计算
            df_asc = df.sort_index(ascending=True)
            self.logger.debug(f"排序后最新5条收盘价:\n{df_asc['收盘'].tail().to_string()}")
            
            exp1 = df_asc['收盘'].ewm(span=12, adjust=False).mean()
            exp2 = df_asc['收盘'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            hist = macd - signal
            
            # 使用最后一条记录（最新数据）
            result = {
                'MACD': float(macd.iloc[-1]),
                'Signal': float(signal.iloc[-1]),
                'Histogram': float(hist.iloc[-1])
            }
            
            self.logger.debug(f"MACD计算结果: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"计算MACD失败: {str(e)}")
            return {'MACD': 0.0, 'Signal': 0.0, 'Histogram': 0.0}
            
    def _calculate_volume_indicators(self, df: pd.DataFrame) -> dict:
        """计算成交量指标
        Args:
            df: 股票数据DataFrame
        Returns:
            包含成交量指标的字典
        """
        try:
            # 将数据按日期升序排列用于计算
            df_asc = df.sort_index(ascending=True)
            
            # 获取最新的成交量数据
            latest_volume = float(df_asc['成交量'].iloc[-1])
            latest_amount = float(df_asc['成交额'].iloc[-1])
            latest_turnover = float(df_asc['换手率'].iloc[-1]) if '换手率' in df_asc.columns else 0.0
            
            # 计算成交量的移动平均
            volume_ma5 = float(df_asc['成交量'].rolling(window=5).mean().iloc[-1])
            volume_ma10 = float(df_asc['成交量'].rolling(window=10).mean().iloc[-1])
            
            return {
                'Volume': format(latest_volume, ',.0f'),
                'Amount': format(latest_amount / 10000, ',.2f') + "万",  # 转换为万元
                'Turnover': round(float(latest_turnover), 2),
                'VolumeMA5': format(volume_ma5, ',.0f'),
                'VolumeMA10': format(volume_ma10, ',.0f')
            }
            
        except Exception as e:
            self.logger.error(f"计算成交量指标时发生错误: {str(e)}")
            return {}
            
    def _get_price_info(self, df: pd.DataFrame) -> Dict[str, float]:
        """获取价格信息"""
        try:
            # 将数据按日期升序排列用于计算
            df_asc = df.sort_index(ascending=True)
            
            # 将 numpy 类型转换为 Python 原生类型
            return {
                'Open': float(df_asc['开盘'].iloc[-1]),
                'High': float(df_asc['最高'].iloc[-1]),
                'Low': float(df_asc['最低'].iloc[-1]),
                'Close': float(df_asc['收盘'].iloc[-1]),
                'Change': float(df_asc['涨跌幅'].iloc[-1])
            }
            
        except Exception as e:
            self.logger.error(f"获取价格信息失败: {str(e)}")
            return {
                'Open': 0.0,
                'High': 0.0,
                'Low': 0.0,
                'Close': 0.0,
                'Change': 0.0
            }
            
    def _calculate_bollinger_bands(self, df: pd.DataFrame) -> dict:
        """计算布林带指标"""
        try:
            # 记录计算布林带的数据信息
            self.logger.debug(f"计算布林带使用的数据范围:")
            self.logger.debug(f"数据条数: {len(df)}")
            self.logger.debug(f"最新5条收盘价:\n{df['收盘'].head().to_string()}")
            
            # 将数据按日期升序排列用于计算
            df_asc = df.sort_index(ascending=True)
            self.logger.debug(f"排序后最新5条收盘价:\n{df_asc['收盘'].tail().to_string()}")
            
            # 计算20日移动平均线
            middle_band = df_asc['收盘'].rolling(window=20).mean()
            
            # 计算标准差
            std = df_asc['收盘'].rolling(window=20).std()
            
            # 计算上轨和下轨 (标准差的2倍)
            upper_band = middle_band + (std * 2)
            lower_band = middle_band - (std * 2)
            
            # 使用最后一条记录（最新数据）
            latest = {
                'upper': round(float(upper_band.iloc[-1]), 2),
                'middle': round(float(middle_band.iloc[-1]), 2),
                'lower': round(float(lower_band.iloc[-1]), 2)
            }
            
            self.logger.debug(f"布林带计算结果: {latest}")
            return latest
            
        except Exception as e:
            self.logger.error(f"计算布林带时发生错误: {str(e)}")
            return {}
            
    def test_stock_data_retrieval(self):
        """测试股票数据获取功能"""
        test_cases = [
            # 上证主板
            {"code": "600000", "name": "浦发银行", "market": "主板"},
            # 深证主板
            {"code": "000001", "name": "平安银行", "market": "主板"},
            # 创业板
            {"code": "300750", "name": "宁德时代", "market": "创业板"},
            # 科创板
            {"code": "688981", "name": "中芯国际", "market": "科创板"}
        ]
        
        for case in test_cases:
            self.logger.info(f"\n开始测试 {case['market']} 股票: {case['name']}({case['code']})")
            
            try:
                # 获取技术指标
                indicators = self.get_technical_indicators(case['code'])
                
                if not indicators:
                    self.logger.error(f"获取 {case['name']} 的技术指标失败")
                    continue
                
                # 验证关键指标是否存在
                required_indicators = ['MA', 'MACD', 'RSI', 'BOLL']
                missing_indicators = [ind for ind in required_indicators if ind not in indicators]
                
                if missing_indicators:
                    self.logger.error(f"缺少必要的技术指标: {missing_indicators}")
                else:
                    self.logger.info(f"{case['name']} 的技术指标获取成功")
                    self.logger.debug(f"技术指标详情:\n{json.dumps(indicators, indent=2, ensure_ascii=False)}")
                
            except Exception as e:
                self.logger.error(f"测试 {case['name']} 时发生错误: {str(e)}")
                self.logger.debug(f"错误详情:\n{traceback.format_exc()}")
                
        self.logger.info("\n测试完成") 