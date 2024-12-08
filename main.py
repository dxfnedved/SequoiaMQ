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
from logger_manager import LoggerManager
import traceback

def job():
    if utils.is_weekday():
        workflow = work_flow.WorkFlow()
        workflow.prepare()

def main():
    # 初始化日志管理器
    logger_manager = LoggerManager()
    logger = logger_manager.get_logger("main")
    
    try:
        # 初始化配置
        settings.init()
        
        # 检查是否有命令行参数
        if len(sys.argv) > 1 and sys.argv[1] == '--gui':
            # GUI模式
            app = stock_selector.QApplication(sys.argv)
            app.setStyle('Fusion')  # 设置应用样式
            
            window = stock_selector.StockSelector()
            window.show()
            sys.exit(app.exec())
        else:
            # 传统模式
            if settings.config['cron']:
                EXEC_TIME = "15:15"
                schedule.every().day.at(EXEC_TIME).do(job)

                while True:
                    schedule.run_pending()
                    time.sleep(1)
            else:
                workflow = work_flow.WorkFlow()
                workflow.prepare()
                
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
