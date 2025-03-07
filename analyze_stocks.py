#!/usr/bin/env python
"""
股票分析工具

可以用于:
1. 更新LSTM数据集
2. 运行LSTM预测
3. 查看预测结果
"""

import os
import sys
import argparse
import subprocess
import json
import logging
from datetime import datetime
import pandas as pd
import glob

# 配置日志
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

log_filename = f"analyze_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_path = os.path.join(log_dir, log_filename)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_path, mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger('analyzer')

def update_lstm_data():
    """更新LSTM数据集"""
    logger.info("开始更新LSTM数据...")
    
    update_data_cmd = []
    if sys.platform == 'win32':
        update_data_cmd = ["cmd.exe", "/c", "update_lstm_data.bat"]
        shell = True
    else:
        update_data_cmd = ["bash", "update_lstm_data.sh"]
        shell = False
    
    try:
        result = subprocess.run(
            update_data_cmd, 
            check=True, 
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        logger.info("LSTM数据更新完成")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"LSTM数据更新失败: {str(e)}")
        logger.error(f"错误输出: {e.output.decode('utf-8', errors='replace') if e.output else 'None'}")
        return False

def run_lstm_predict(stock_codes):
    """运行LSTM预测"""
    if not stock_codes:
        logger.error("没有提供股票代码，无法运行预测")
        return False
    
    logger.info(f"开始预测以下股票: {', '.join(stock_codes)}")
    
    lstm_cmd = [sys.executable, "-m", "LSTM.batch_predict"] + stock_codes
    
    try:
        result = subprocess.run(
            lstm_cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        logger.info("LSTM预测完成")
        logger.info(result.stdout.decode('utf-8', errors='replace'))
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"LSTM预测失败: {str(e)}")
        if e.output:
            logger.error(f"错误输出: {e.output.decode('utf-8', errors='replace')}")
        return False

def get_stock_codes_from_watchlist():
    """从watchlist.json中获取股票代码"""
    watchlist_path = "watchlist.json"
    if not os.path.exists(watchlist_path):
        logger.warning(f"找不到自选股文件: {watchlist_path}")
        return []
    
    try:
        with open(watchlist_path, 'r', encoding='utf-8') as f:
            watchlist = json.load(f)
        
        # 提取股票代码
        stock_codes = []
        if isinstance(watchlist, list):
            # 直接使用列表
            stock_codes = [stock.get('code', '') for stock in watchlist if 'code' in stock]
        elif isinstance(watchlist, dict) and 'stocks' in watchlist:
            # 使用stocks字段
            stock_codes = [stock.get('code', '') for stock in watchlist['stocks'] if 'code' in stock]
        
        # 过滤空值
        stock_codes = [s for s in stock_codes if s]
        
        logger.info(f"从自选股文件中获取到 {len(stock_codes)} 个股票代码")
        return stock_codes
    except Exception as e:
        logger.error(f"读取自选股文件出错: {str(e)}")
        return []

def show_prediction_results(stock_codes=None, limit=10):
    """
    显示预测结果
    
    Args:
        stock_codes: 要显示的股票代码列表，为None则显示所有结果
        limit: 显示的最近预测结果数量限制
    """
    try:
        # 获取预测结果目录
        prediction_dir = os.path.join("LSTM", "predictions")
        if not os.path.exists(prediction_dir):
            logger.error(f"找不到预测结果目录: {prediction_dir}")
            return False
        
        # 获取所有预测结果文件
        prediction_files = glob.glob(os.path.join(prediction_dir, "*.csv"))
        if not prediction_files:
            logger.warning("没有找到任何预测结果文件")
            return False
        
        # 按修改时间排序，最新的在前
        prediction_files.sort(key=os.path.getmtime, reverse=True)
        
        # 限制文件数量
        prediction_files = prediction_files[:limit]
        
        # 显示结果
        print("\n" + "="*80)
        print(f"最近 {len(prediction_files)} 个预测结果:")
        print("="*80)
        
        for idx, file_path in enumerate(prediction_files, 1):
            filename = os.path.basename(file_path)
            stock_code = filename.split('_')[0] if '_' in filename else "Unknown"
            
            # 如果指定了股票代码且当前文件不在列表中，则跳过
            if stock_codes and stock_code not in stock_codes:
                continue
            
            # 读取CSV文件
            try:
                df = pd.read_csv(file_path)
                # 获取最后一行（最新预测）
                last_row = df.iloc[-1] if not df.empty else None
                
                if last_row is not None:
                    modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    print(f"\n{idx}. 股票代码: {stock_code} - 预测于 {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   文件: {filename}")
                    
                    # 显示预测结果
                    prediction_date = last_row.get('ds', 'N/A')
                    predicted_price = last_row.get('yhat', 'N/A')
                    lower_bound = last_row.get('yhat_lower', 'N/A')
                    upper_bound = last_row.get('yhat_upper', 'N/A')
                    
                    print(f"   日期: {prediction_date}")
                    print(f"   预测价格: {predicted_price:.2f}" if isinstance(predicted_price, (int, float)) else f"   预测价格: {predicted_price}")
                    print(f"   价格区间: {lower_bound:.2f} - {upper_bound:.2f}" if isinstance(lower_bound, (int, float)) and isinstance(upper_bound, (int, float)) else f"   价格区间: {lower_bound} - {upper_bound}")
            except Exception as e:
                logger.error(f"读取预测文件 {file_path} 出错: {str(e)}")
                print(f"\n{idx}. 股票代码: {stock_code} - 文件读取失败")
        
        print("\n" + "="*80)
        return True
    except Exception as e:
        logger.error(f"显示预测结果时出错: {str(e)}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="股票分析工具")
    parser.add_argument("--update-data", action="store_true", help="更新LSTM数据集")
    parser.add_argument("--predict", action="store_true", help="运行LSTM预测")
    parser.add_argument("--show-results", action="store_true", help="显示预测结果")
    parser.add_argument("--stock-codes", nargs='+', help="指定要分析的股票代码列表，如 000001 600519")
    parser.add_argument("--limit", type=int, default=10, help="显示的预测结果数量限制")
    args = parser.parse_args()
    
    # 如果没有指定任何操作，显示帮助信息
    if not (args.update_data or args.predict or args.show_results):
        parser.print_help()
        return
    
    # 更新数据
    if args.update_data:
        update_lstm_data()
    
    # 获取股票代码
    stock_codes = args.stock_codes
    if not stock_codes and (args.predict or args.show_results):
        stock_codes = get_stock_codes_from_watchlist()
        
        if not stock_codes:
            logger.warning("未提供股票代码且未找到自选股列表")
            if args.predict:
                logger.error("无法运行预测，请提供股票代码")
                return
    
    # 运行预测
    if args.predict and stock_codes:
        run_lstm_predict(stock_codes)
    
    # 显示结果
    if args.show_results:
        show_prediction_results(stock_codes, args.limit)

if __name__ == "__main__":
    main() 