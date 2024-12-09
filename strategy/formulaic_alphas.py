# -*- encoding: UTF-8 -*-
import os
import pandas as pd
from datetime import datetime
import talib as tl
import logging
import numpy as np
from collections import defaultdict
import time
import data_fetcher
import push
from logger_manager import LoggerManager

# 创建专门的logger
logger = logging.getLogger('Alpha_Strategy')

# 参数设置
PRICE_LIMIT = 0.1  # 涨跌停限制 10%
VOL_THRESHOLD = 2.0  # 成交量放大倍数阈值
MA_PERIODS = [5, 10, 20]  # 均线周期

# 添加结果保存目录
RESULTS_DIR = "results"

class Alpha101Strategy:
    """Alpha101 因子策略"""
    
    def __init__(self, logger_manager=None):
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("Alpha101_Strategy")

    def analyze(self, data):
        """分析股票数据"""
        try:
            if data is None or data.empty:
                self.logger.error("数据为空，无法分析")
                return None
                
            # 检查必要的列是否存在
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in data.columns for col in required_columns):
                self.logger.error("数据缺少必要的列")
                return None
            
            result = {}
            
            # 计算Alpha因子
            alpha_factors = self.calculate_alpha_factors(data)
            if alpha_factors:
                result.update(alpha_factors)
            
            # 生成交易信号
            signals = self.generate_signals(alpha_factors)
            if signals:
                result.update(signals)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Alpha101策略分析失败: {str(e)}")
            return None

    def calculate_alpha_factors(self, data):
        """计算Alpha因子"""
        try:
            result = {}
            
            # 计算收益率和波动率
            returns = data['Close'].pct_change()
            volatility = returns.rolling(window=20).std()
            
            # Alpha1: 处理收益率为负时的波动率
            condition = returns < 0
            combined = pd.Series(index=data.index)
            combined[condition] = volatility[condition]
            combined[~condition] = data['Close'][~condition] ** 2
            alpha1 = self.ts_argmax_rank(combined, 5)
            
            # Alpha2: 成交量和价格变化的相关性
            volume_delta = np.log(data['Volume']).diff(2)
            price_change = (data['Close'] - data['Open']) / data['Open']
            alpha2 = -1 * self.correlation_rank(volume_delta, price_change, 6)
            
            # Alpha3: 开盘价和成交量的相关性
            alpha3 = -1 * self.correlation_rank(data['Open'], data['Volume'], 10)
            
            # Alpha4: 最低价的时序排名
            alpha4 = -1 * self.ts_rank(data['Low'], 9)
            
            # 汇总结果
            result.update({
                'Alpha1': round(alpha1.iloc[-1], 4) if not pd.isna(alpha1.iloc[-1]) else 0,
                'Alpha2': round(alpha2.iloc[-1], 4) if not pd.isna(alpha2.iloc[-1]) else 0,
                'Alpha3': round(alpha3.iloc[-1], 4) if not pd.isna(alpha3.iloc[-1]) else 0,
                'Alpha4': round(alpha4.iloc[-1], 4) if not pd.isna(alpha4.iloc[-1]) else 0
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"计算Alpha因子失败: {str(e)}")
            return {}

    def generate_signals(self, factors):
        """生成交易信号"""
        try:
            result = {}
            signals = []
            
            if not factors:
                return {}
            
            # Alpha1信号
            alpha1 = factors.get('Alpha1', 0)
            if abs(alpha1) > 1.5:
                signals.append(f"Alpha1{'看多' if alpha1 > 0 else '看空'}")
            
            # Alpha2信号
            alpha2 = factors.get('Alpha2', 0)
            if abs(alpha2) > 0.8:
                signals.append(f"Alpha2{'看多' if alpha2 > 0 else '看空'}")
            
            # Alpha3信号
            alpha3 = factors.get('Alpha3', 0)
            if abs(alpha3) > 0.7:
                signals.append(f"Alpha3{'看多' if alpha3 > 0 else '看空'}")
            
            # Alpha4信号
            alpha4 = factors.get('Alpha4', 0)
            if abs(alpha4) > 0.6:
                signals.append(f"Alpha4{'看多' if alpha4 > 0 else '看空'}")
            
            if signals:
                result['Alpha101_信号'] = '; '.join(signals)
            
            return result
            
        except Exception as e:
            self.logger.error(f"生成Alpha信号失败: {str(e)}")
            return {}

    def ts_argmax_rank(self, series, window):
        """计算时序最大值排名"""
        try:
            result = pd.Series(index=series.index)
            for i in range(window, len(series)):
                try:
                    window_data = series.iloc[i-window:i]
                    # 处理无效值
                    valid_data = window_data.dropna()
                    if len(valid_data) < 2:  # 至少需要2个有效值
                        result.iloc[i] = np.nan
                        continue
                        
                    # 计算最大值的位置
                    max_pos = valid_data.values.argmax()
                    result.iloc[i] = len(valid_data) - max_pos  # 转换为排名
                except Exception as e:
                    self.logger.debug(f"计算窗口 {i} 的最大值排名失败: {str(e)}")
                    result.iloc[i] = np.nan
                    
            return result
        except Exception as e:
            self.logger.error(f"计算时序最大值排名失败: {str(e)}")
            return pd.Series(index=series.index)

    def correlation_rank(self, x, y, window):
        """计算排名相关系数"""
        try:
            result = pd.Series(index=x.index)
            for i in range(window, len(x)):
                try:
                    x_window = x.iloc[i-window:i].rank()
                    y_window = y.iloc[i-window:i].rank()
                    
                    # 处理无效值
                    valid_mask = ~(x_window.isna() | y_window.isna())
                    if valid_mask.sum() < 2:  # 至少需要2个有效值
                        result.iloc[i] = np.nan
                        continue
                        
                    x_valid = x_window[valid_mask].values
                    y_valid = y_window[valid_mask].values
                    
                    # 计算相关系数
                    x_mean = np.mean(x_valid)
                    y_mean = np.mean(y_valid)
                    x_std = np.std(x_valid)
                    y_std = np.std(y_valid)
                    
                    # 处理标准差为0的情况
                    if x_std == 0 or y_std == 0:
                        result.iloc[i] = np.nan
                        continue
                    
                    # 手动计算相关系数，避免使用 np.corrcoef
                    x_centered = x_valid - x_mean
                    y_centered = y_valid - y_mean
                    correlation = np.sum(x_centered * y_centered) / (x_std * y_std * (len(x_valid) - 1))
                    
                    # 确保结果在[-1, 1]范围内
                    correlation = np.clip(correlation, -1.0, 1.0)
                    result.iloc[i] = correlation
                    
                except Exception as e:
                    self.logger.debug(f"计算窗口 {i} 的相关系数失败: {str(e)}")
                    result.iloc[i] = np.nan
                    
            return result
        except Exception as e:
            self.logger.error(f"计算排名相关系数失败: {str(e)}")
            return pd.Series(index=x.index)

    def ts_rank(self, series, window):
        """计算时序排名"""
        try:
            result = pd.Series(index=series.index)
            for i in range(window, len(series)):
                try:
                    window_data = series.iloc[i-window:i]
                    # 处理无效值
                    valid_data = window_data.dropna()
                    if len(valid_data) < 2:  # 至少需要2个有效值
                        result.iloc[i] = np.nan
                        continue
                        
                    result.iloc[i] = valid_data.rank().iloc[-1]
                except Exception as e:
                    self.logger.debug(f"计算窗口 {i} 的排名失败: {str(e)}")
                    result.iloc[i] = np.nan
                    
            return result
        except Exception as e:
            self.logger.error(f"计算时序排名失败: {str(e)}")
            return pd.Series(index=series.index)

def ensure_dir_exists(directory):
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def save_strategy_results(stock_signals, date_str):
    """保存策略结果到CSV文件"""
    ensure_dir_exists(RESULTS_DIR)
    
    # 创建结果DataFrame
    results = []
    for code, signals in stock_signals.items():
        stock_code, stock_name = code
        for strategy, signal in signals:
            if signal == "买入":
                results.append({
                    '日期': date_str,
                    '股票代码': stock_code,
                    '股票名称': stock_name,
                    '策略': strategy,
                    '信号': signal
                })
    
    if results:
        df = pd.DataFrame(results)
        file_path = os.path.join(RESULTS_DIR, f'strategy_signals_{date_str}.csv')
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        logging.info(f"策略信号已保存到: {file_path}")

def save_statistics_results(stats_data, date_str):
    """保存市场���计数据到CSV"""
    ensure_dir_exists(RESULTS_DIR)
    
    file_path = os.path.join(RESULTS_DIR, f'market_stats_{date_str}.csv')
    pd.DataFrame([stats_data]).to_csv(file_path, index=False, encoding='utf-8-sig')
    logging.info(f"市场统计数据已保存到: {file_path}")

def process(stocks, strategies):
    date_str = datetime.now().strftime('%Y%m%d')
    stocks_data = data_fetcher.run(stocks)
    stock_signals = defaultdict(list)
    strategy_stats = defaultdict(int)
    
    for strategy, strategy_func in strategies.items():
        results = check_strategy(stocks_data, strategy, strategy_func)
        for code, signal in results.items():
            stock_signals[code].append((strategy, signal))
            if signal == "买入":
                strategy_stats[strategy] += 1
        time.sleep(2)
    
    # 保存策略信号
    save_strategy_results(stock_signals, date_str)
    
    # 输出简要统计信息到日志
    logging.info("--- 策略统计 ---")
    for strategy, count in strategy_stats.items():
        logging.info(f"{strategy}: {count}个买入信号")

def statistics(all_data, stocks):
    date_str = datetime.now().strftime('%Y%m%d')
    
    stats_data = {
        '日期': date_str,
        '涨停数量': len(all_data.loc[(all_data['涨跌幅'] >= 9.5)]),
        '跌停数���': len(all_data.loc[(all_data['涨跌幅'] <= -9.5)]),
        '涨幅大于5%数量': len(all_data.loc[(all_data['涨跌幅'] >= 5)]),
        '跌幅大于5%数量': len(all_data.loc[(all_data['涨跌幅'] <= -5)]),
        '总股票数量': len(stocks)
    }
    
    # 保存统计数据
    save_statistics_results(stats_data, date_str)
    
    # 发送消息通知
    msg = ("涨停数：{涨停数量}   跌停数：{跌停数量}\n"
           "涨幅大于5%数：{涨幅大于5%数量}  跌幅大于5%数量：{跌幅大于5%数量}").format(**stats_data)
    push.statistics(msg)

def handle_limit_up_down(data):
    """处理涨跌停限制"""
    data['涨跌幅'] = data['收盘'].pct_change()
    data['涨跌幅'] = data['涨跌幅'].clip(-PRICE_LIMIT, PRICE_LIMIT)
    return data

def handle_suspension(data):
    """处理停牌"""
    return data[data['成交量'] > 0].copy()

def calculate_alpha1(data):
    """Alpha#1: (rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)"""
    # 确保数据是pandas Series
    returns = pd.Series(data['p_change'] / 100)
    close = pd.Series(data['收盘'])
    
    # 计算20日收益率标准差
    stddev = returns.rolling(window=20).std()
    
    # 构建条件数组
    condition = returns < 0
    result = pd.Series(np.where(condition, stddev, close))
    
    # 计算SignedPower
    signed_power = pd.Series(np.sign(result) * (np.abs(result) ** 2))
    
    # 计算5日内最大值的位置
    ts_argmax = signed_power.rolling(window=5).apply(np.argmax)
    
    return ts_argmax

def calculate_volume_factor(data):
    """成交量因子：量价相关性"""
    volume = data['成交量']
    close = data['收盘']
    
    # 计算成交量变化
    vol_ma5 = volume.rolling(window=5).mean()
    vol_ratio = volume / vol_ma5
    
    # 计算价格动量
    price_momentum = close.pct_change(5)
    
    return vol_ratio * np.sign(price_momentum)

def calculate_reversal_factor(data):
    """反转因子：超跌反弹"""
    high = data['最高']
    low = data['最���']
    close = data['收盘']
    
    # 计算超跌程度
    hl_range = (high - low) / low
    close_position = (close - low) / (high - low)
    
    return -1 * close_position * hl_range

def check_buy_signals(code, data, end_date=None):
    """买入信号判断"""
    try:
        # 数据预处理
        data = handle_limit_up_down(data)
        data = handle_suspension(data)
        
        if len(data) < 30:
            return False, {}
        
        # 计算因子
        data['alpha1'] = calculate_alpha1(data)
        data['volume_factor'] = calculate_volume_factor(data)
        data['reversal_factor'] = calculate_reversal_factor(data)
        
        # 获取最新数据
        current = data.iloc[-1]
        prev = data.iloc[-2]
        
        # 买入条件
        conditions = [
            current['alpha1'] > prev['alpha1'],  # 动量上升
            current['volume_factor'] > VOL_THRESHOLD,  # 成交量放大
            current['reversal_factor'] < -0.2,  # 超跌反弹机会
            current['成交量'] > data['成交量'].rolling(window=20).mean().iloc[-1],  # 放量
            all(current['收盘'] > data[f'MA{period}'].iloc[-1] for period in MA_PERIODS)  # 均线多头
        ]
        
        if all(conditions):
            signal_info = {
                '动量': current['alpha1'],
                '量价': current['volume_factor'],
                '反转': current['reversal_factor']
            }
            return True, signal_info
            
    except Exception as e:
        logger.error(f"处理股票{code}时出错：{str(e)}")
        return False, {}
    
    return False, {}

def check_sell_signals(code, data, end_date=None):
    """卖出信号判断"""
    try:
        # 数据预处理
        data = handle_limit_up_down(data)
        data = handle_suspension(data)
        
        if len(data) < 30:
            return False, {}
        
        # 计算因子
        data['alpha1'] = calculate_alpha1(data)
        data['volume_factor'] = calculate_volume_factor(data)
        data['reversal_factor'] = calculate_reversal_factor(data)
        
        # 获取最新数据
        current = data.iloc[-1]
        prev = data.iloc[-2]
        
        # 卖出条件
        conditions = [
            current['alpha1'] < prev['alpha1'],  # 动量下降
            current['volume_factor'] < 0.5,  # 量能萎缩
            current['reversal_factor'] > 0.2,  # 上涨乏力
            current['成交量'] < data['成交量'].rolling(window=20).mean().iloc[-1],  # 缩量
            any(current['收盘'] < data[f'MA{period}'].iloc[-1] for period in MA_PERIODS)  # 跌���均线
        ]
        
        if any(conditions):
            signal_info = {
                '动量': current['alpha1'],
                '量价': current['volume_factor'],
                '反转': current['reversal_factor']
            }
            return True, signal_info
            
    except Exception as e:
        logger.error(f"处理股票{code}时出错：{str(e)}")
        return False, {}
    
    return False, {}

def check(code, data, end_date=None):
    """主要的策略判断函数"""
    buy_signal, buy_info = check_buy_signals(code, data, end_date)
    sell_signal, sell_info = check_sell_signals(code, data, end_date)
    
    # 记录详细信号信息到CSV
    if buy_signal or sell_signal:
        signal_info = buy_info if buy_signal else sell_info
        save_signal_details(code, "买入" if buy_signal else "卖出", signal_info)
    
    return buy_signal

def save_signal_details(code, signal_type, signal_info):
    """保存详细的信号信息"""
    date_str = datetime.now().strftime('%Y%m%d')
    file_path = os.path.join('results', 'alpha_signals_details.csv')
    
    data = {
        '日期': date_str,
        '股票代码': code,
        '信号类型': signal_type,
        **signal_info
    }
    
    # 追加模式写入CSV
    df = pd.DataFrame([data])
    if os.path.exists(file_path):
        df.to_csv(file_path, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        df.to_csv(file_path, index=False, encoding='utf-8-sig')

def check_strategy(stocks_data, strategy_name, strategy_func):
    """检查策略的买入卖出信号"""
    results = {}
    for code, data in stocks_data.items():
        try:
            if strategy_func(code, data):
                results[code] = "买入"
        except Exception as e:
            logger.error(f"策略{strategy_name}处理股票{code}时出错：{str(e)}")
    return results
