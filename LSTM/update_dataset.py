#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n"""\n更新LSTM模型数据集至最新日期\n"""

import sys
import os
import argparse
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import json
import akshare as ak
from tqdm import tqdm
import numpy as np
import traceback
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入自定义模块
from data_loader import StockDataLoader
from logger_manager import LoggerManager

def validate_data_quality(df, stock_code, logger=None):
    """
    验证数据质量，检查数据连续性和完整性
    
    参数:
        df (pd.DataFrame): 股票数据
        stock_code (str): 股票代码
        logger: 日志记录器
        
    返回:
        tuple: (是否有效, 问题描述)
    """
    if logger is None:
        logger = logging.getLogger("validate_data")
    
    try:
        # 检查数据是否为空
        if df is None or df.empty:
            return False, "数据为空"
        
        # 检查必要列是否存在
        required_columns = ['日期', '开盘', '收盘', '最高', '最低', '成交量']
        for col in required_columns:
            if col not in df.columns:
                return False, f"缺少必要列: {col}"
        
        # 检查是否有足够的数据点
        if len(df) < 60:  # 至少需要60个交易日数据
            return False, f"数据点不足60天，实际: {len(df)}天"
        
        # 检查数据连续性 - 交易日间隔
        df['日期'] = pd.to_datetime(df['日期'])
        df = df.sort_values('日期')
        
        # 计算日期间隔（工作日）
        df['日期间隔'] = df['日期'].diff().dt.days
        
        # 提取大于3天的间隔（排除周末）
        large_gaps = df[df['日期间隔'] > 3]['日期间隔'].tolist()
        
        # 如果大间隔过多，则标记为可能有问题
        if len(large_gaps) > 10:
            gap_info = ", ".join([f"{gap}天" for gap in large_gaps[:5]]) + f" 等{len(large_gaps)}处"
            logger.warning(f"股票 {stock_code} 数据存在较多日期间隔: {gap_info}")
        
        # 检查异常值 - 价格为0或者异常高
        price_zero = (df['收盘'] == 0).sum()
        if price_zero > 0:
            logger.warning(f"股票 {stock_code} 有 {price_zero} 条收盘价为0的记录")
        
        # 检查成交量异常
        volume_zero = (df['成交量'] == 0).sum()
        if volume_zero > 5:  # 允许少量停牌
            logger.warning(f"股票 {stock_code} 有 {volume_zero} 条成交量为0的记录")
        
        # 检查最近数据是否更新（最后一条记录应该是最近的交易日）
        last_date = df['日期'].max()
        today = pd.Timestamp(datetime.now().date())
        days_diff = (today - last_date).days
        
        # 如果最后一条数据超过7天，且不是节假日期间，标记为可能过期
        if days_diff > 7:
            logger.warning(f"股票 {stock_code} 数据可能过期，最后交易日: {last_date.strftime('%Y-%m-%d')}, 间隔: {days_diff}天")
        
        return True, "数据有效"
    
    except Exception as e:
        error_msg = f"验证数据质量时出错: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return False, error_msg

def update_stock_dataset(stock_code, days=1825, cache_dir="cache", logger=None):
    """
    更新指定股票的数据集
    
    参数:
        stock_code (str): 股票代码
        days (int): 获取的历史数据天数，默认5年(1825天)
        cache_dir (str): 缓存目录
        logger: 日志记录器
    
    返回:
        bool: 更新是否成功
    """
    try:
        # 初始化数据加载器
        data_loader = StockDataLoader(logger_manager=logger.logger_manager if logger else None)
        
        # 确保股票代码格式正确
        formatted_code = data_loader.format_stock_code(stock_code)
        
        # 设置日期范围
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        end_date = datetime.now().strftime('%Y%m%d')
        
        if logger:
            logger.info(f"正在更新股票 {formatted_code} 数据，时间范围: {start_date} 到 {end_date}")
        else:
            print(f"正在更新股票 {formatted_code} 数据，时间范围: {start_date} 到 {end_date}")
        
        # 获取股票数据
        df = data_loader.get_stock_data(formatted_code, start_date, end_date)
        
        # 验证数据质量
        is_valid, message = validate_data_quality(df, formatted_code, logger)
        if not is_valid:
            if logger:
                logger.error(f"股票 {formatted_code} 数据质量检查失败: {message}")
            else:
                print(f"股票 {formatted_code} 数据质量检查失败: {message}")
            return False
        
        # 确保缓存目录存在
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        
        # 保存数据到缓存
        cache_file = cache_path / f"{formatted_code}_data.csv"
        df.to_csv(cache_file)
        
        # 记录元数据
        metadata = {
            "stock_code": formatted_code,
            "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "start_date": start_date,
            "end_date": end_date,
            "record_count": len(df),
            "data_quality": {
                "has_missing_values": df.isnull().any().any(),
                "date_range": {
                    "start": df.index.min().strftime('%Y-%m-%d') if not df.empty else None,
                    "end": df.index.max().strftime('%Y-%m-%d') if not df.empty else None
                },
                "features": list(df.columns)
            }
        }
        
        with open(cache_path / f"{formatted_code}_metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
        
        if logger:
            logger.info(f"股票 {formatted_code} 数据更新成功，共 {len(df)} 条记录，已保存到 {cache_file}")
            logger.info(f"数据时间范围: {metadata['data_quality']['date_range']['start']} 到 {metadata['data_quality']['date_range']['end']}")
        else:
            print(f"股票 {formatted_code} 数据更新成功，共 {len(df)} 条记录，已保存到 {cache_file}")
            print(f"数据时间范围: {metadata['data_quality']['date_range']['start']} 到 {metadata['data_quality']['date_range']['end']}")
        
        return True
    
    except Exception as e:
        error_msg = f"更新股票 {stock_code} 数据时出错: {str(e)}"
        if logger:
            logger.error(error_msg)
            logger.error(traceback.format_exc())
        else:
            print(error_msg)
            print(traceback.format_exc())
        return False

def get_all_stocks():
    """
    获取所有A股股票列表
    
    返回:
        list: 股票代码列表
    """
    try:
        # 获取A股股票列表
        df = ak.stock_zh_a_spot_em()
        # 提取股票代码
        stock_list = df['代码'].tolist()
        return stock_list
    except Exception as e:
        print(f"获取股票列表时出错: {str(e)}")
        return []

def get_stock_from_watchlist(watchlist_path="watchlist.json"):
    """
    从自选股列表中获取股票
    
    参数:
        watchlist_path (str): 自选股文件路径
    
    返回:
        list: 自选股股票代码列表
    """
    try:
        # 确保文件存在
        if not os.path.exists(watchlist_path):
            # 尝试查找根目录下的watchlist.json
            root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            watchlist_path = os.path.join(root_path, 'watchlist.json')
            if not os.path.exists(watchlist_path):
                print(f"未找到自选股文件: {watchlist_path}")
                return []
        
        # 读取自选股文件
        with open(watchlist_path, 'r', encoding='utf-8') as f:
            watchlist = json.load(f)
        
        # 提取股票代码
        if isinstance(watchlist, list):
            # 直接使用列表
            stocks = [stock.get('code', '') for stock in watchlist if 'code' in stock]
        elif isinstance(watchlist, dict) and 'stocks' in watchlist:
            # 使用stocks字段
            stocks = [stock.get('code', '') for stock in watchlist['stocks'] if 'code' in stock]
        else:
            print(f"自选股文件格式不支持: {watchlist_path}")
            return []
        
        # 过滤空值
        stocks = [s for s in stocks if s]
        return stocks
    
    except Exception as e:
        print(f"读取自选股列表时出错: {str(e)}")
        return []

def update_all_datasets(stocks=None, days=1825, cache_dir="cache", batch_size=50, watchlist_only=False):
    """
    更新所有股票的数据集
    
    参数:
        stocks (list): 股票代码列表，如果为None则获取所有A股
        days (int): 获取的历史数据天数，默认5年(1825天)
        cache_dir (str): 缓存目录
        batch_size (int): 批处理大小
        watchlist_only (bool): 是否只更新自选股
    """
    # 初始化日志
    logger_manager = LoggerManager()
    logger = logger_manager.get_logger("update_dataset")
    
    # 获取股票列表
    if stocks is None:
        if watchlist_only:
            logger.info("从自选股获取股票列表...")
            stocks = get_stock_from_watchlist()
            if not stocks:
                logger.warning("自选股列表为空，将获取所有A股")
                stocks = get_all_stocks()
        else:
            logger.info("正在获取所有A股股票列表...")
            stocks = get_all_stocks()
    
    if not stocks:
        logger.error("获取股票列表失败")
        return
    
    logger.info(f"开始更新 {len(stocks)} 只股票的数据集")
    
    # 分批处理
    total_batches = (len(stocks) + batch_size - 1) // batch_size
    successful = 0
    failed = 0
    
    # 创建进度条
    with tqdm(total=len(stocks), desc="更新数据集") as pbar:
        for i in range(0, len(stocks), batch_size):
            batch = stocks[i:i+batch_size]
            logger.info(f"处理批次 {i//batch_size + 1}/{total_batches}, 本批次包含 {len(batch)} 只股票")
            
            for stock_code in batch:
                result = update_stock_dataset(stock_code, days, cache_dir, logger)
                if result:
                    successful += 1
                else:
                    failed += 1
                pbar.update(1)
    
    logger.info(f"数据集更新完成. 成功: {successful}, 失败: {failed}")
    print(f"\n数据集更新完成. 成功: {successful}, 失败: {failed}")
    
    # 返回更新统计
    return {
        "total": len(stocks),
        "successful": successful,
        "failed": failed,
        "completion_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "days_range": days
    }

def check_data_freshness(cache_dir="cache", max_days=7):
    """
    检查数据新鲜度，返回需要更新的股票列表
    
    参数:
        cache_dir (str): 缓存目录
        max_days (int): 最大允许的天数差异
    
    返回:
        list: 需要更新的股票代码列表
    """
    try:
        # 初始化日志
        logger_manager = LoggerManager()
        logger = logger_manager.get_logger("update_dataset")
        
        # 确保缓存目录存在
        cache_path = Path(cache_dir)
        if not cache_path.exists():
            logger.warning(f"缓存目录不存在: {cache_dir}")
            return []
        
        need_update = []
        now = datetime.now()
        
        # 获取所有元数据文件
        metadata_files = list(cache_path.glob("*_metadata.json"))
        logger.info(f"找到 {len(metadata_files)} 个元数据文件")
        
        for metadata_file in metadata_files:
            try:
                # 读取元数据
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # 获取股票代码
                stock_code = metadata.get("stock_code", "")
                if not stock_code:
                    continue
                
                # 检查更新时间
                update_time_str = metadata.get("update_time", "")
                if not update_time_str:
                    need_update.append(stock_code)
                    continue
                
                # 计算时间差异
                update_time = datetime.strptime(update_time_str, '%Y-%m-%d %H:%M:%S')
                days_diff = (now - update_time).days
                
                # 如果超过最大天数，添加到需要更新的列表
                if days_diff > max_days:
                    logger.info(f"股票 {stock_code} 数据需要更新，上次更新时间: {update_time_str}，已过 {days_diff} 天")
                    need_update.append(stock_code)
            
            except Exception as e:
                logger.error(f"处理元数据文件 {metadata_file} 时出错: {str(e)}")
                continue
        
        logger.info(f"发现 {len(need_update)} 只股票数据需要更新")
        return need_update
    
    except Exception as e:
        logger.error(f"检查数据新鲜度时出错: {str(e)}")
        return []

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="更新LSTM模型数据集")
    parser.add_argument("--stock", type=str, help="单只股票代码")
    parser.add_argument("--all", action="store_true", help="更新所有A股数据")
    parser.add_argument("--watchlist", action="store_true", help="只更新自选股数据")
    parser.add_argument("--check-freshness", action="store_true", help="检查数据新鲜度并更新过期数据")
    parser.add_argument("--days", type=int, default=1825, help="获取的历史数据天数，默认5年(1825天)")
    parser.add_argument("--cache-dir", type=str, default="cache", help="缓存目录")
    parser.add_argument("--batch-size", type=int, default=50, help="批处理大小")
    parser.add_argument("--max-days", type=int, default=7, help="数据新鲜度检查的最大天数，默认7天")
    args = parser.parse_args()
    
    # 初始化日志
    logger_manager = LoggerManager()
    logger = logger_manager.get_logger("update_dataset")
    
    # 记录开始时间
    start_time = datetime.now()
    logger.info(f"开始执行数据更新，时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    stats = None
    
    if args.stock:
        # 更新单只股票
        logger.info(f"更新单只股票: {args.stock}")
        result = update_stock_dataset(args.stock, args.days, args.cache_dir, logger)
        stats = {
            "total": 1,
            "successful": 1 if result else 0,
            "failed": 0 if result else 1,
            "completion_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "days_range": args.days
        }
        print(f"数据更新{'成功' if result else '失败'}")
    
    elif args.check_freshness:
        # 检查数据新鲜度并更新
        logger.info(f"正在检查数据新鲜度，最大允许天数: {args.max_days}")
        need_update = check_data_freshness(args.cache_dir, args.max_days)
        
        if need_update:
            logger.info(f"需要更新 {len(need_update)} 只股票数据")
            stats = update_all_datasets(need_update, args.days, args.cache_dir, args.batch_size)
        else:
            logger.info("所有数据均为最新，无需更新")
            stats = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "completion_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "days_range": args.days,
                "status": "all_fresh"
            }
    
    elif args.watchlist:
        # 只更新自选股
        logger.info("更新自选股数据")
        stats = update_all_datasets(None, args.days, args.cache_dir, args.batch_size, watchlist_only=True)
    
    elif args.all:
        # 更新所有股票
        logger.info("更新所有A股数据")
        stats = update_all_datasets(None, args.days, args.cache_dir, args.batch_size)
    
    else:
        print("请指定 --stock 参数更新单只股票，--watchlist 更新自选股，--all 更新所有股票，或 --check-freshness 检查数据新鲜度")
        logger.warning("未指定任何操作，脚本退出")
    
    # 记录结束时间和耗时
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"数据更新完成，耗时: {duration:.2f} 秒")
    
    # 保存执行统计信息
    if stats:
        stats_file = os.path.join(args.cache_dir, f"update_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            os.makedirs(args.cache_dir, exist_ok=True)
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    **stats,
                    "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "duration_seconds": duration
                }, f, ensure_ascii=False, indent=4)
            logger.info(f"执行统计信息已保存到: {stats_file}")
        except Exception as e:
            logger.error(f"保存执行统计信息时出错: {str(e)}")

if __name__ == "__main__":
    main()
