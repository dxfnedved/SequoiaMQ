# -*- encoding: UTF-8 -*-

import utils
import work_flow
import settings
import schedule
import time
import datetime
from pathlib import Path
import sys
import stock_selector
from PySide6.QtWidgets import QApplication
from logger_manager import LoggerManager
import traceback

def job():
    """定时任务"""
    if utils.is_weekday():
        print("开始执行定时任务...")
        workflow = work_flow.WorkFlow()
        workflow.prepare()
        print("定时任务执行完成")

def main():
    # 初始化日志管理器
    logger_manager = LoggerManager()
    logger = logger_manager.get_logger("main")
    
    try:
        print("正在初始化系统...")
        # 初始化配置
        config = settings.init()
        print("配置加载完成")
        
        # 检查是否有命令行参数
        if len(sys.argv) > 1 and sys.argv[1] == '--gui':
            # GUI模式
            print("启动GUI模式...")
            app = QApplication(sys.argv)
            app.setStyle('Fusion')  # 设置应用样式
            
            window = stock_selector.StockSelector()
            window.show()
            sys.exit(app.exec())
        else:
            # 命令行模式
            print("启动命令行模式")
            logger.info("启动命令行模式")
            if config.get('cron', False):
                # 定时任务模式
                EXEC_TIME = config.get('exec_time', "15:15")
                print(f"启动定时任务模式，执行时间：{EXEC_TIME}")
                logger.info(f"启动定时任务模式，执行时间：{EXEC_TIME}")
                schedule.every().day.at(EXEC_TIME).do(job)
                
                while True:
                    schedule.run_pending()
                    time.sleep(1)
            else:
                # 直接执行模式
                print("开始执行分析任务...")
                logger.info("开始执行分析任务...")
                workflow = work_flow.WorkFlow()
                workflow.prepare()
                print("分析任务完成")
                logger.info("分析任务完成")
                
    except Exception as e:
        error_msg = f"程序运行出错: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
