# -*- coding: UTF-8 -*-
import datetime
import akshare as ak
from logger_manager import LoggerManager
import os
import time
import json
import traceback
from colorama import Fore, Style

logger = LoggerManager().get_logger("utils")

def is_weekday():
    """是否是工作日"""
    return datetime.datetime.today().weekday() < 5

def is_stock_active(code, name=None):
    """检查股票是否处于正常交易状态"""
    try:
        # 获取股票的基本信息
        stock_info = ak.stock_individual_info_em(symbol=code)
        if stock_info is None or stock_info.empty:
            logger.warning(f"无法获取股票 {code} 的基本信息")
            return False
            
        # 检查数据格式
        if '股票状态' not in stock_info.columns:
            # 尝试获取实时行情作为备选验证方法
            try:
                realtime_info = ak.stock_zh_a_spot_em()
                if realtime_info is not None and not realtime_info.empty:
                    stock_data = realtime_info[realtime_info['代码'] == code]
                    if not stock_data.empty:
                        # 如果能获取到实时行情，说明股票可交易
                        return True
            except Exception as e:
                logger.warning(f"获取股票 {code} 实时行情失败: {str(e)}")
            
            # 如果两种方法都失败，使用基本过滤规则
            if name:
                # 检查基本规则
                if 'ST' in name.upper() or '退' in name:
                    return False
                # 检查股票代码规则
                if code.startswith(('000', '001', '002', '003', '300', '600', '601', '603', '605')):
                    return True
            return False
            
        # 如果有状态信息，检查是否为正常交易
        status = stock_info.iloc[0]['股票状态']
        if '正常交易' not in str(status):
            logger.info(f"股票 {code} 状态为: {status}")
            return False
            
        # 额外的检查
        if name and ('退' in name or 'ST' in name.upper()):
            return False
            
        return True
        
    except Exception as e:
        logger.warning(f"检查股票 {code} 状态时出错: {str(e)}")
        # 发生错误时，尝试使用基本规则判断
        if name:
            if 'ST' in name.upper() or '退' in name:
                return False
            if code.startswith(('000', '001', '002', '003', '300', '600', '601', '603', '605')):
                return True
        return False

def get_stock_list():
    """获取有效的A股列表（剔除ST、退市、科创板和北交所股票）"""
    max_retries = 3
    retry_delay = 0.01
    
    for attempt in range(max_retries):
        try:
            print(f"\n正在获取A股列表 (尝试 {attempt + 1}/{max_retries})...")
            logger.info(f"开始获取A股列表 (尝试 {attempt + 1}/{max_retries})...")
            
            # 获取所有A股列表
            stock_info = ak.stock_zh_a_spot_em()
            
            if stock_info is None or stock_info.empty:
                print("获取股票列表失败：返回数据为空")
                logger.error("获取股票列表失败：返回数据为空")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # 指数退避
                    continue
                return []
                
            # 只保留股票代码和名称
            stock_info = stock_info[['代码', '名称']]
            stock_info = stock_info.rename(columns={'代码': 'code', '名称': 'name'})
            
            # 过滤条件
            def is_valid_stock(code, name):
                # 基本过滤条件
                if not code.startswith(('000', '001', '002', '003', '300', '600', '601', '603', '605')):
                    return False
                    
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
                    
                # 检查股票是否处于正常交易状态
                return is_stock_active(code, name)
                
            # 应用过滤条件
            valid_stocks = stock_info[
                stock_info.apply(lambda x: is_valid_stock(x['code'], x['name']), axis=1)
            ]
            
            # 转换为列表格式
            stock_list = valid_stocks.to_dict('records')
            
            # 记录统计信息
            stats = f"""
A股列表获取成功:
- 原始数量: {len(stock_info)}
- 有效数量: {len(stock_list)}
- 过滤掉的股票: {len(stock_info) - len(stock_list)}
- 市场分布:
  主板: {len(valid_stocks[valid_stocks['code'].str.match('^(000|001|600|601)', na=False)])}
  中小板: {len(valid_stocks[valid_stocks['code'].str.match('^(002|003)', na=False)])}
  创业板: {len(valid_stocks[valid_stocks['code'].str.match('^300', na=False)])}
            """
            print(stats)
            logger.info(stats)
            
            return stock_list
            
        except Exception as e:
            print(f"获取股票列表失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            logger.error(f"获取股票列表失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            logger.error(traceback.format_exc())
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))  # 指数退避
            else:
                return []
                
    return []

def format_code(code):
    """式化股票代码（添加市场标识）"""
    if code.startswith(('000', '001', '002', '003', '300')):
        return f"0.{code}"  # 深市
    elif code.startswith(('600', '601', '603', '605')):
        return f"1.{code}"  # 沪市
    return code

def is_market_open():
    """检查当前是否是交易时间"""
    try:
        # 获取当前时间
        now = datetime.datetime.now()
        
        # 如果是周末，返回False
        if now.weekday() >= 5:
            return False
            
        # 获取当前日期的交易状态
        today_str = now.strftime('%Y%m%d')
        calendar_df = ak.tool_trade_date_hist_sina()
        
        if calendar_df is None or calendar_df.empty:
            return False
            
        # 检查今天是否是交易日
        if today_str not in calendar_df['trade_date'].values:
            return False
            
        # 检查当前时间是否在交易时间内
        morning_start = datetime.datetime.strptime(f"{today_str} 09:30:00", "%Y%m%d %H:%M:%S")
        morning_end = datetime.datetime.strptime(f"{today_str} 11:30:00", "%Y%m%d %H:%M:%S")
        afternoon_start = datetime.datetime.strptime(f"{today_str} 13:00:00", "%Y%m%d %H:%M:%S")
        afternoon_end = datetime.datetime.strptime(f"{today_str} 15:00:00", "%Y%m%d %H:%M:%S")
        
        return (morning_start <= now <= morning_end) or (afternoon_start <= now <= afternoon_end)
        
    except Exception as e:
        print(f"检查市场状态时出错: {str(e)}")
        return False

def get_market_status():
    """获取市场状态信息"""
    try:
        now = datetime.datetime.now()
        today_str = now.strftime('%Y%m%d')
        
        # 获取交易日历
        calendar_df = ak.tool_trade_date_hist_sina()
        
        if calendar_df is None or calendar_df.empty:
            return {
                'is_open': False,
                'next_open': None,
                'message': "无法获取交易日历"
            }
            
        # 检查今天是否是交易日
        is_trading_day = today_str in calendar_df['trade_date'].values
        
        # 获取下一个交易日
        future_dates = calendar_df[calendar_df['trade_date'] > today_str]
        next_trading_day = future_dates.iloc[0]['trade_date'] if not future_dates.empty else None
        
        # 检查当前时间
        current_time = now.time()
        morning_session = (
            datetime.datetime.strptime("09:30", "%H:%M").time() <= current_time <= 
            datetime.datetime.strptime("11:30", "%H:%M").time()
        )
        afternoon_session = (
            datetime.datetime.strptime("13:00", "%H:%M").time() <= current_time <= 
            datetime.datetime.strptime("15:00", "%H:%M").time()
        )
        
        # 确定市场状态
        if not is_trading_day:
            status = {
                'is_open': False,
                'next_open': next_trading_day,
                'message': "今日休市"
            }
        elif morning_session or afternoon_session:
            status = {
                'is_open': True,
                'session': "上午" if morning_session else "下午",
                'message': "交易中"
            }
        else:
            if current_time < datetime.datetime.strptime("09:30", "%H:%M").time():
                status = {
                    'is_open': False,
                    'next_open': today_str,
                    'message': "等待开盘"
                }
            elif datetime.datetime.strptime("11:30", "%H:%M").time() < current_time < datetime.datetime.strptime("13:00", "%H:%M").time():
                status = {
                    'is_open': False,
                    'next_open': today_str,
                    'message': "午间休市"
                }
            else:
                status = {
                    'is_open': False,
                    'next_open': next_trading_day,
                    'message': "已收盘"
                }
                
        return status
        
    except Exception as e:
        return {
            'is_open': False,
            'error': str(e),
            'message': "获取市场状态失败"
        }

def calculate_indicators(data):
    """计算技术指标"""
    try:
        df = data.copy()
        
        # 计算移动平均线
        for period in [5, 10, 20, 30, 60]:
            df[f'MA{period}'] = df['close'].rolling(window=period).mean()
            
        # 计算MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']
        
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 计算布林带
        df['BB_Middle'] = df['close'].rolling(window=20).mean()
        df['BB_Upper'] = df['BB_Middle'] + 2 * df['close'].rolling(window=20).std()
        df['BB_Lower'] = df['BB_Middle'] - 2 * df['close'].rolling(window=20).std()
        
        # 计算成交量变化
        df['Volume_MA5'] = df['volume'].rolling(window=5).mean()
        df['Volume_MA10'] = df['volume'].rolling(window=10).mean()
        df['Volume_Ratio'] = df['volume'] / df['Volume_MA5']
        
        return df
        
    except Exception as e:
        print(f"计算技术指标时出错: {str(e)}")
        return None

def save_analysis_result(result, code):
    """保存分析结果"""
    try:
        # 创建结果目录
        result_dir = 'data/analysis_results'
        os.makedirs(result_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{result_dir}/analysis_{code}_{timestamp}.json"
        
        # 添加元数据
        result['metadata'] = {
            'code': code,
            'analysis_time': timestamp,
            'version': '1.0'
        }
        
        # 保存结果
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        return filename
        
    except Exception as e:
        print(f"保存分析结果时出错: {str(e)}")
        return None

def get_stock_name_dict():
    """获取股票代码到名称的映射字典"""
    try:
        logger.info("开始获取股票名称字典...")
        
        # 获取所有A股列表
        stock_info = ak.stock_zh_a_spot_em()
        
        if stock_info is None or stock_info.empty:
            logger.error("获取股票名称字典失败：返回数据为空")
            return {}
            
        # 只保留股票代码和名称
        stock_info = stock_info[['代码', '名称']]
        
        # 转换为字典格式
        stock_dict = dict(zip(stock_info['代码'], stock_info['名称']))
        
        logger.info(f"成功获取 {len(stock_dict)} 只股票的名称信息")
        
        return stock_dict
        
    except Exception as e:
        logger.error(f"获取股票名称字典失败: {str(e)}")
        logger.error(traceback.format_exc())
        return {}

def get_stock_info():
    """获取A股列表（已剔除ST、退市、科创板和北交所股票）"""
    logger = LoggerManager().get_logger("utils")
    max_retries = 3
    retry_delay = 0.1
    
    for attempt in range(max_retries):

        print(f"{Fore.CYAN}正在从接口获取股票列表...{Style.RESET_ALL}")
        # 获取股票列表
        stock_info = ak.stock_zh_a_spot_em()
            
        if stock_info is None or stock_info.empty:
            raise ValueError("获取到的股票列表为空")
                
            # 获取已退市股票列表
        try:
            delisted = ak.stock_info_sz_delist("终止上市公司")
            delisted_codes = set(delisted['证券代码'].astype(str).str.zfill(6))
                
                # delisted_sh = ak.stock_info_sh_delist()
                # delisted_codes.update(delisted_sh['COMPANY_CODE'].astype(str).str.zfill(6))
        except Exception as e:
            logger.warning(f"获取退市股票列表失败: {str(e)}")
            delisted_codes = set()
                
            # 获取新股列表
            # try:
            #     new_stocks = ak.stock_zh_a_new()
            #     not_listed = set(new_stocks[~new_stocks['上市日期'].notna()]['代码'].astype(str))
            # except Exception as e:
            #     logger.warning(f"获取新股列表失败: {str(e)}")
            #     not_listed = set()
            
            # 预先过滤掉不需要的股票
        stock_info = stock_info[
                # 只保留主板、中小板、创业板
            stock_info['代码'].str.match('^(000|001|002|003|300|600|601|603|605)') &
                # 排除ST股票
            ~stock_info['名称'].str.contains('ST', case=False) &
                # 排除退市股票
            ~stock_info['名称'].str.contains('退') &
                # 排除科创板
            ~stock_info['代码'].str.startswith('688') &
                # 排除北交所
            ~stock_info['代码'].str.startswith('8') &
                # 排除已知退市股票
            ~stock_info['代码'].isin(delisted_codes) 
                # 排除未上市新股
                # ~stock_info['代码'].isin(not_listed)
            ]
            
            # 进一步验证股票状态
        valid_stocks = []
        for _, row in stock_info.iterrows():
            code = row['代码']
            name = row['名称']
                
                # try:
                #     # # 获取股票最新行情以验证是否可交易
                    # quote = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
                    # if quote is None or quote.empty:
                    #     logger.warning(f"股票 {code} ({name}) 无法获取行情数据，可能已退市或未上市")
                    #     continue
                        
            market_type = 'main' if code.startswith(('000', '001', '600', '601')) else \
                            'sme' if code.startswith(('002', '003')) else \
                            'gem' if code.startswith('300') else 'other'
                                
            valid_stocks.append({
                    'code': code,
                    'name': name,
                    'market': market_type
                })
                # except Exception as e:
                #     logger.warning(f"验证股票 {code} ({name}) 状态失败: {str(e)}")
                #     continue
            
            # 统计信息
        main_board = len([s for s in valid_stocks if s['market'] == 'main'])
        sme_board = len([s for s in valid_stocks if s['market'] == 'sme'])
        gem_board = len([s for s in valid_stocks if s['market'] == 'gem'])
            
        stats = f"""
{Fore.GREEN}A股列表获取成功:{Style.RESET_ALL}
{Fore.CYAN}- 原始数量: {len(stock_info)}
- 有效数量: {len(valid_stocks)}
- 过滤掉的股票: {len(stock_info) - len(valid_stocks)}
- 市场分布:
  主板: {main_board}
  中小板: {sme_board}
  创业板: {gem_board}{Style.RESET_ALL}
"""
        print(stats)
        logger.info(stats)
            
        return valid_stocks
            
    #     except Exception as e:
    #         print(f"{Fore.RED}获取股票列表失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}{Style.RESET_ALL}")
    #         logger.error(f"获取股票列表失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
    #         logger.error(traceback.format_exc())
    #         if attempt < max_retries - 1:
    #             time.sleep(retry_delay * (2 ** attempt))  # 指数退避
    #         else:
    #             return []
                
    # return []