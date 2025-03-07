#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LSTM预测结果可视化模块

此模块提供多种可视化功能，用于展示LSTM模型的预测结果：
1. 生成单只股票的预测趋势图
2. 批量生成多只股票的预测趋势图
3. 生成预测结果的统计摘要报告
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import glob
import logging
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 设置中文字体支持
try:
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体
    plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题
except Exception as e:
    logger.warning(f"设置中文字体失败: {str(e)}")
    logger.warning("图表中的中文可能无法正确显示")

# 图表样式配置
plt.style.use('ggplot')
CHART_DPI = 100
CHART_SIZE = (12, 7)
COLORS = {
    'actual': '#1f77b4',   # 蓝色
    'predict': '#ff7f0e',  # 橙色
    'up': '#2ca02c',       # 绿色
    'down': '#d62728',     # 红色
    'neutral': '#7f7f7f'   # 灰色
}

def load_prediction(stock_code):
    """
    加载指定股票的预测数据
    
    Args:
        stock_code (str): 股票代码
        
    Returns:
        pd.DataFrame or None: 包含预测数据的DataFrame，如果数据不存在则返回None
    """
    try:
        # 构建预测文件路径
        pred_file = os.path.join("LSTM", "predictions", f"{stock_code}_prediction.csv")
        
        # 检查文件是否存在
        if not os.path.exists(pred_file):
            logger.warning(f"股票 {stock_code} 的预测数据不存在")
            return None
        
        # 读取预测数据
        pred_data = pd.read_csv(pred_file, parse_dates=['date'])
        
        # 基本数据检查
        if pred_data.empty:
            logger.warning(f"股票 {stock_code} 的预测数据为空")
            return None
            
        # 确保数据包含必要的列
        required_cols = ['date', 'actual', 'prediction']
        if not all(col in pred_data.columns for col in required_cols):
            logger.warning(f"股票 {stock_code} 的预测数据缺少必要的列: {required_cols}")
            return None
            
        return pred_data
        
    except Exception as e:
        logger.error(f"加载股票 {stock_code} 的预测数据时出错: {str(e)}")
        return None

def plot_prediction(stock_code, save_path=None, show_plot=False):
    """
    绘制预测数据的图表
    
    Args:
        stock_code (str): 股票代码
        save_path (str, optional): 保存图表的路径，默认为None
        show_plot (bool, optional): 是否显示图表，默认为False
        
    Returns:
        bool: 是否成功创建图表
    """
    # 加载预测数据
    pred_data = load_prediction(stock_code)
    if pred_data is None:
        return False
    
    try:
        # 创建图表
        fig, ax = plt.subplots(figsize=CHART_SIZE, dpi=CHART_DPI)
        
        # 绘制实际价格线
        ax.plot(pred_data['date'], pred_data['actual'], 
                label='实际价格', color=COLORS['actual'], 
                linewidth=2, marker='o', markersize=4)
        
        # 绘制预测价格线
        ax.plot(pred_data['date'], pred_data['prediction'], 
                label='预测价格', color=COLORS['predict'], 
                linewidth=2, marker='s', markersize=4, 
                linestyle='--')
        
        # 计算预测准确度
        pred_direction = np.sign(pred_data['prediction'].diff())
        actual_direction = np.sign(pred_data['actual'].diff())
        correct_direction = (pred_direction == actual_direction).sum()
        direction_accuracy = correct_direction / (len(pred_data) - 1) * 100 if len(pred_data) > 1 else 0
        
        # 计算最后一个预测点的未来趋势
        last_prediction = pred_data['prediction'].iloc[-1]
        last_actual = pred_data['actual'].iloc[-1]
        trend_direction = "上涨" if last_prediction > last_actual else "下跌" if last_prediction < last_actual else "持平"
        trend_color = COLORS['up'] if trend_direction == "上涨" else COLORS['down'] if trend_direction == "下跌" else COLORS['neutral']
        
        # 计算统计数据
        mse = ((pred_data['prediction'] - pred_data['actual'])**2).mean()
        rmse = np.sqrt(mse)
        mae = np.abs(pred_data['prediction'] - pred_data['actual']).mean()
        
        # 设置图表标题和标签
        ax.set_title(f'股票 {stock_code} LSTM预测分析\n'
                     f'预测趋势: {trend_direction} | 方向准确率: {direction_accuracy:.2f}%',
                     fontsize=14, pad=10, color=trend_color, fontweight='bold')
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('价格', fontsize=12)
        
        # 添加网格线
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # 格式化X轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate()
        
        # 添加图例
        ax.legend(loc='best', fontsize=12)
        
        # 添加统计信息文本框
        stats_text = (
            f'RMSE: {rmse:.4f}\n'
            f'MAE: {mae:.4f}\n'
            f'方向准确率: {direction_accuracy:.2f}%\n'
            f'预测点数: {len(pred_data)}'
        )
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.02, 0.05, stats_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='bottom', bbox=props)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path)
            logger.info(f"图表已保存至 {save_path}")
        
        # 显示图表
        if show_plot:
            plt.show()
        
        plt.close(fig)
        return True
        
    except Exception as e:
        logger.error(f"绘制股票 {stock_code} 的预测图表时出错: {str(e)}")
        plt.close()
        return False

def get_all_prediction_files():
    """
    获取所有预测文件
    
    Returns:
        list: 预测文件路径列表
    """
    prediction_dir = os.path.join("LSTM", "predictions")
    if not os.path.exists(prediction_dir):
        logger.warning(f"预测目录不存在: {prediction_dir}")
        return []
        
    prediction_files = glob.glob(os.path.join(prediction_dir, "*_prediction.csv"))
    return prediction_files

def get_stock_codes_from_prediction_files():
    """
    从预测文件中提取股票代码
    
    Returns:
        list: 股票代码列表
    """
    prediction_files = get_all_prediction_files()
    stock_codes = []
    
    for file_path in prediction_files:
        file_name = os.path.basename(file_path)
        # 从文件名中提取股票代码
        if "_prediction.csv" in file_name:
            stock_code = file_name.replace("_prediction.csv", "")
            stock_codes.append(stock_code)
    
    return stock_codes

def generate_all_charts(stock_codes=None):
    """
    生成所有股票的预测图表
    
    Args:
        stock_codes (list, optional): 股票代码列表，默认为None，表示生成所有预测文件的图表
        
    Returns:
        tuple: (成功计数, 失败计数)
    """
    # 如果未提供股票代码，则获取所有预测文件的股票代码
    if stock_codes is None:
        stock_codes = get_stock_codes_from_prediction_files()
    
    if not stock_codes:
        logger.warning("没有找到需要生成图表的股票")
        return 0, 0
    
    # 创建保存图表的目录
    charts_dir = os.path.join("LSTM", "charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    success_count = 0
    failed_count = 0
    
    # 使用tqdm显示进度条
    for stock_code in tqdm(stock_codes, desc="生成预测图表"):
        save_path = os.path.join(charts_dir, f"{stock_code}_prediction_chart.png")
        if plot_prediction(stock_code, save_path):
            success_count += 1
        else:
            failed_count += 1
    
    logger.info(f"图表生成完成: 成功 {success_count} 个, 失败 {failed_count} 个")
    logger.info(f"图表保存在目录: {os.path.abspath(charts_dir)}")
    
    return success_count, failed_count

def generate_summary_report(output_file=None):
    """
    生成预测摘要报告
    
    Args:
        output_file (str, optional): 报告输出文件路径，默认为None，将在LSTM/reports目录下创建一个时间戳文件
        
    Returns:
        str: 报告文件路径
    """
    stock_codes = get_stock_codes_from_prediction_files()
    
    if not stock_codes:
        logger.warning("没有找到预测数据，无法生成报告")
        return None
    
    # 创建报告目录
    reports_dir = os.path.join("LSTM", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # 如果未指定输出文件，则创建一个带时间戳的文件名
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(reports_dir, f"prediction_report_{timestamp}.csv")
    
    try:
        # 收集每只股票的预测统计数据
        report_data = []
        
        for stock_code in tqdm(stock_codes, desc="分析预测数据"):
            pred_data = load_prediction(stock_code)
            if pred_data is None:
                continue
                
            # 计算方向准确度
            pred_direction = np.sign(pred_data['prediction'].diff())
            actual_direction = np.sign(pred_data['actual'].diff())
            correct_direction = (pred_direction == actual_direction).sum()
            direction_accuracy = correct_direction / (len(pred_data) - 1) * 100 if len(pred_data) > 1 else 0
            
            # 计算最后一个预测点的未来趋势
            last_prediction = pred_data['prediction'].iloc[-1]
            last_actual = pred_data['actual'].iloc[-1]
            last_date = pred_data['date'].iloc[-1]
            trend_change = (last_prediction - last_actual) / last_actual * 100
            trend_direction = "上涨" if trend_change > 0 else "下跌" if trend_change < 0 else "持平"
            
            # 计算统计数据
            mse = ((pred_data['prediction'] - pred_data['actual'])**2).mean()
            rmse = np.sqrt(mse)
            mae = np.abs(pred_data['prediction'] - pred_data['actual']).mean()
            
            # 构建报告数据
            report_data.append({
                '股票代码': stock_code,
                '最新日期': last_date,
                '实际价格': last_actual,
                '预测价格': last_prediction,
                '预测变动(%)': trend_change,
                '趋势方向': trend_direction,
                '方向准确率(%)': direction_accuracy,
                'RMSE': rmse,
                'MAE': mae,
                '数据点数': len(pred_data)
            })
        
        # 创建报告DataFrame
        if not report_data:
            logger.warning("没有有效的预测数据，无法生成报告")
            return None
            
        report_df = pd.DataFrame(report_data)
        
        # 按预测变动百分比排序
        report_df = report_df.sort_values('预测变动(%)', ascending=False)
        
        # 保存报告
        report_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"预测摘要报告已保存至 {output_file}")
        
        # 创建HTML版本的报告 (更易于阅读)
        html_file = output_file.replace('.csv', '.html')
        report_df.to_html(html_file, index=False, encoding='utf-8')
        logger.info(f"HTML格式的报告已保存至 {html_file}")
        
        # 创建一个总结文本报告
        txt_file = output_file.replace('.csv', '.txt')
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("LSTM预测摘要报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"分析股票总数: {len(report_df)}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("TOP 5 看涨股票:\n")
            top_up = report_df.nlargest(5, '预测变动(%)')
            for _, row in top_up.iterrows():
                f.write(f"  {row['股票代码']}: 预测变动 {row['预测变动(%)']:.2f}%, 方向准确率 {row['方向准确率(%)']:.2f}%\n")
            
            f.write("\nTOP 5 看跌股票:\n")
            top_down = report_df.nsmallest(5, '预测变动(%)')
            for _, row in top_down.iterrows():
                f.write(f"  {row['股票代码']}: 预测变动 {row['预测变动(%)']:.2f}%, 方向准确率 {row['方向准确率(%)']:.2f}%\n")
            
            f.write("\n预测方向准确率最高的股票:\n")
            top_accuracy = report_df.nlargest(5, '方向准确率(%)')
            for _, row in top_accuracy.iterrows():
                f.write(f"  {row['股票代码']}: 方向准确率 {row['方向准确率(%)']:.2f}%, 预测变动 {row['预测变动(%)']:.2f}%\n")
            
            f.write("\n统计摘要:\n")
            f.write(f"  平均方向准确率: {report_df['方向准确率(%)'].mean():.2f}%\n")
            f.write(f"  平均RMSE: {report_df['RMSE'].mean():.4f}\n")
            f.write(f"  平均MAE: {report_df['MAE'].mean():.4f}\n")
            f.write(f"  看涨股票数量: {(report_df['预测变动(%)'] > 0).sum()}\n")
            f.write(f"  看跌股票数量: {(report_df['预测变动(%)'] < 0).sum()}\n")
            
        logger.info(f"文本摘要报告已保存至 {txt_file}")
        
        return output_file
        
    except Exception as e:
        logger.error(f"生成预测摘要报告时出错: {str(e)}")
        return None

def get_stock_codes_from_watchlist():
    """
    从watchlist.json文件中获取股票代码
    
    Returns:
        list: 股票代码列表
    """
    watchlist_file = "watchlist.json"
    if not os.path.exists(watchlist_file):
        logger.warning(f"自选股文件不存在: {watchlist_file}")
        return []
        
    try:
        with open(watchlist_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 处理不同格式的watchlist.json
        if isinstance(data, list):
            # 直接是股票列表
            stocks = data
        elif isinstance(data, dict) and "stocks" in data:
            # 包含"stocks"键的字典
            stocks = data.get("stocks", [])
        else:
            logger.warning(f"无法识别的watchlist.json格式")
            return []
            
        # 提取股票代码
        stock_codes = [s.get('code', '') for s in stocks if 'code' in s]
        return [code for code in stock_codes if code]  # 过滤掉空字符串
        
    except Exception as e:
        logger.error(f"从watchlist.json获取股票代码时出错: {str(e)}")
        return []

def main():
    """主函数，处理命令行参数并执行相应的功能"""
    parser = argparse.ArgumentParser(description='LSTM预测结果可视化工具')
    
    # 添加命令行参数
    parser.add_argument('--stock', type=str, help='单个股票代码，用于生成单只股票的预测图表')
    parser.add_argument('--stocks', type=str, nargs='+', help='多个股票代码，用于批量生成预测图表')
    parser.add_argument('--all', action='store_true', help='生成所有预测股票的图表')
    parser.add_argument('--report', action='store_true', help='生成预测摘要报告')
    parser.add_argument('--watchlist', action='store_true', help='从watchlist.json获取股票代码并生成图表')
    parser.add_argument('--show', action='store_true', help='显示图表而非保存文件')
    
    args = parser.parse_args()
    
    # 检查是否提供了任何参数
    if not any([args.stock, args.stocks, args.all, args.report, args.watchlist]):
        parser.print_help()
        return
    
    # 处理单只股票图表生成
    if args.stock:
        stock_code = args.stock
        if args.show:
            logger.info(f"显示股票 {stock_code} 的预测图表")
            plot_prediction(stock_code, show_plot=True)
        else:
            charts_dir = os.path.join("LSTM", "charts")
            os.makedirs(charts_dir, exist_ok=True)
            save_path = os.path.join(charts_dir, f"{stock_code}_prediction_chart.png")
            logger.info(f"生成股票 {stock_code} 的预测图表")
            plot_prediction(stock_code, save_path)
    
    # 处理多只股票图表生成
    if args.stocks:
        stock_codes = args.stocks
        logger.info(f"生成 {len(stock_codes)} 只股票的预测图表")
        generate_all_charts(stock_codes)
    
    # 处理自选股票图表生成
    if args.watchlist:
        stock_codes = get_stock_codes_from_watchlist()
        if stock_codes:
            logger.info(f"从自选股列表中找到 {len(stock_codes)} 只股票")
            generate_all_charts(stock_codes)
        else:
            logger.warning("自选股列表为空或无法读取")
    
    # 处理所有股票图表生成
    if args.all:
        logger.info("生成所有预测股票的图表")
        generate_all_charts()
    
    # 处理报告生成
    if args.report:
        logger.info("生成预测摘要报告")
        generate_summary_report()

if __name__ == "__main__":
    main() 