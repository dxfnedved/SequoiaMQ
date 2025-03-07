#!/usr/bin/env python
"""
项目启动脚本

同时启动API服务器和前端开发服务器
"""

import os
import sys
import subprocess
import time
import threading
import signal
import argparse
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('start.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger('starter')

def run_api_server():
    """启动API服务器"""
    logger.info("启动API服务器...")
    python_executable = sys.executable
    api_server_cmd = [python_executable, "-m", "api_server.start_server", "--reload"]
    logger.info(f"执行命令: {' '.join(api_server_cmd)}")
    process = subprocess.Popen(
        api_server_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    logger.info(f"API服务器进程ID: {process.pid}")
    return process

def run_frontend():
    """启动前端开发服务器"""
    logger.info("启动前端开发服务器...")
    # 保存当前目录
    current_dir = os.getcwd()
    # 切换到前端目录
    frontend_dir = os.path.join(current_dir, "frontend-vue")
    logger.info(f"前端目录: {frontend_dir}")
    
    # 使用cmd执行npm命令，确保命令能正确执行
    if sys.platform == 'win32':
        # 在Windows上使用cmd.exe确保npm命令能正确执行
        cmd = ["cmd.exe", "/c", "npm run serve"]
        shell = True
    else:
        cmd = ["npm", "run", "serve"]
        shell = False
    
    logger.info(f"执行前端命令: {cmd}")
    # 启动进程
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=shell,
        cwd=frontend_dir  # 设置工作目录
    )
    
    logger.info(f"前端服务器进程ID: {process.pid}")
    # 切回原目录
    os.chdir(current_dir)
    return process

def run_lstm_predict(stock_codes=None, foreground=False):
    """
    运行LSTM预测
    
    Args:
        stock_codes: 需要预测的股票代码列表
        foreground: 是否在前台运行（显示输出）
    
    Returns:
        如果在后台运行，返回进程对象；如果在前台运行，返回None
    """
    if not stock_codes:
        # 尝试从watchlist.json中获取股票代码
        stock_codes = get_stock_codes_from_watchlist()
        if not stock_codes:
            logger.warning("没有找到任何股票代码用于LSTM预测")
            return None
    
    logger.info(f"开始LSTM预测，股票: {', '.join(stock_codes)}")
    
    lstm_cmd = [sys.executable, "-m", "LSTM.batch_predict"] + stock_codes
    
    if foreground:
        # 在前台运行，显示输出
        try:
            subprocess.run(lstm_cmd, check=True)
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"LSTM预测失败: {str(e)}")
            return None
    else:
        # 在后台运行
        try:
            lstm_process = subprocess.Popen(
                lstm_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            logger.info(f"LSTM预测进程ID: {lstm_process.pid}")
            return lstm_process
        except Exception as e:
            logger.error(f"启动LSTM预测进程失败: {str(e)}")
            return None

def update_lstm_data(update_method="watchlist", days=1825, check_freshness=True, max_days=3):
    """
    更新LSTM数据
    
    参数:
        update_method (str): 更新方法，可选值为"watchlist"、"all"或"freshness"
        days (int): 历史数据天数
        check_freshness (bool): 是否检查数据新鲜度
        max_days (int): 数据新鲜度最大天数
        
    返回:
        bool: 更新是否成功
    """
    logger.info("正在更新LSTM数据...")
    update_data_cmd = []
    
    if sys.platform == 'win32':
        python_cmd = [sys.executable, "LSTM/update_dataset.py"]
        shell = False
    else:
        python_cmd = [sys.executable, "LSTM/update_dataset.py"]
        shell = False
    
    # 添加命令行参数
    if update_method == "all":
        python_cmd.append("--all")
    elif update_method == "watchlist":
        python_cmd.append("--watchlist")
    
    if check_freshness:
        python_cmd.append("--check-freshness")
        python_cmd.extend(["--max-days", str(max_days)])
        
    python_cmd.extend(["--days", str(days)])
    
    try:
        logger.info(f"执行命令: {' '.join(python_cmd)}")
        result = subprocess.run(
            python_cmd, 
            check=True, 
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        output = result.stdout.decode('utf-8', errors='replace')
        logger.info(f"LSTM数据更新输出:\n{output}")
        logger.info("LSTM数据更新完成")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"LSTM数据更新失败: {str(e)}")
        logger.error(f"错误输出: {e.output.decode('utf-8', errors='replace') if e.output else 'None'}")
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

def output_reader(process, prefix):
    """读取进程输出并打印到控制台"""
    while True:
        output = process.stdout.readline()
        if not output and process.poll() is not None:
            break
        if output:
            try:
                line = output.decode('utf-8', errors='replace').strip()
                if line:
                    logger.info(f"[{prefix}] {line}")
            except Exception as e:
                logger.error(f"[{prefix}] 解码输出时出错: {str(e)}")

def handle_shutdown(processes):
    """处理关闭进程"""
    logger.info("\n正在关闭服务...")
    for name, process in processes.items():
        if process and process.poll() is None:
            logger.info(f"关闭 {name} 进程...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"强制终止 {name} 进程...")
                process.kill()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="启动SequoiaMQ前后端服务")
    parser.add_argument("--api-only", action="store_true", help="仅启动API服务器")
    parser.add_argument("--frontend-only", action="store_true", help="仅启动前端服务器")
    parser.add_argument("--update-data", action="store_true", help="启动前更新LSTM数据")
    parser.add_argument("--update-lstm-data", action="store_true", help="启动前更新LSTM数据集至最新日期（处理更多历史数据）")
    parser.add_argument("--update-all-stocks", action="store_true", help="更新所有股票的LSTM数据")
    parser.add_argument("--days", type=int, default=730, help="LSTM历史数据天数，默认2年(730天)")
    parser.add_argument("--max-days", type=int, default=3, help="LSTM数据新鲜度检查的最大天数")
    parser.add_argument("--lstm-predict", action="store_true", help="启动时运行LSTM预测")
    parser.add_argument("--lstm-predict-only", action="store_true", help="只运行LSTM预测，不启动其他服务")
    parser.add_argument("--stock-codes", nargs='+', help="指定要预测的股票代码列表，如 000001 600519")
    parser.add_argument("--performance-mode", action="store_true", help="高性能模式，优化内存和CPU使用")
    parser.add_argument("--debug", action="store_true", help="调试模式，显示详细日志")
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("调试模式已启用")
    
    processes = {}
    threads = []
    
    try:
        # 如果只运行LSTM预测
        if args.lstm_predict_only:
            stock_codes = args.stock_codes if args.stock_codes else get_stock_codes_from_watchlist()
            if stock_codes:
                logger.info(f"仅运行LSTM预测，股票: {', '.join(stock_codes)}")
                run_lstm_predict(stock_codes, foreground=True)
            else:
                logger.error("未指定股票代码且未找到自选股列表，无法运行LSTM预测")
            return
        
        # 数据更新
        if args.update_data or args.update_lstm_data:
            update_method = "all" if args.update_all_stocks else "watchlist"
            days = args.days
            update_lstm_data(update_method=update_method, days=days, max_days=args.max_days)
        
        # 启动API服务器
        if not args.api_only:
            api_process = run_api_server()
            processes["API服务器"] = api_process
            api_thread = threading.Thread(
                target=output_reader,
                args=(api_process, "API服务器"),
                daemon=True
            )
            api_thread.start()
            threads.append(api_thread)
            
            # 等待API服务器启动
            logger.info("等待API服务器启动...")
            time.sleep(3)
        
        # 启动前端服务器
        if not args.frontend_only:
            frontend_process = run_frontend()
            processes["前端服务器"] = frontend_process
            frontend_thread = threading.Thread(
                target=output_reader,
                args=(frontend_process, "前端服务器"),
                daemon=True
            )
            frontend_thread.start()
            threads.append(frontend_thread)
        
        logger.info("\n所有服务已启动，按Ctrl+C停止...\n")
        
        # 设置信号处理函数
        def signal_handler(sig, frame):
            handle_shutdown(processes)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 等待所有进程完成
        while True:
            all_exited = True
            for name, process in processes.items():
                if process.poll() is None:
                    all_exited = False
                    break
            
            if all_exited:
                logger.info("所有服务已退出")
                break
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\n接收到中断信号")
    except Exception as e:
        logger.error(f"启动服务出错: {str(e)}")
    finally:
        handle_shutdown(processes)

if __name__ == "__main__":
    main() 