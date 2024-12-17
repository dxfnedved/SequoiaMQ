# -*- encoding: UTF-8 -*-

import os
import sys
from datetime import datetime
from work_flow import WorkFlow
from logger_manager import LoggerManager
import traceback
from PySide6.QtWidgets import QApplication
from GUI import MainWindow

def setup_environment():
    """设置运行环境"""
    try:
        # 创建必要的目录
        for dir_name in ['data', 'logs', 'cache', 'summary']:
            os.makedirs(dir_name, exist_ok=True)
            
        # 设置日志
        log_file = f'logs/main_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        logger_manager = LoggerManager(log_file)
        logger = logger_manager.get_logger("main")
        
        return logger_manager, logger
        
    except Exception as e:
        print(f"设置运行环境失败: {str(e)}")
        raise

def main():
    """主函数"""
    try:
        # 设置环境
        logger_manager, logger = setup_environment()
        logger.info("正在初始化系统...")
        
        # 检查运行模式
        is_gui_mode = len(sys.argv) > 1 and sys.argv[1] == '--gui'
        mode = "GUI模式" if is_gui_mode else "命令行模式"
        logger.info(f"启动{mode}")
        
        if is_gui_mode:
            # GUI模式
            app = QApplication(sys.argv)
            window = MainWindow()
            window.show()
            return app.exec_()
        else:
            # 命令行模式
            workflow = WorkFlow(logger_manager=logger_manager)
            
            # 执行分析任务
            logger.info("开始执行分析任务...")
            success = workflow.prepare()
            
            if success:
                logger.info("分析任务成功完成")
                return 0
            else:
                logger.error("分析任务执行失败")
                return 1
                
    except Exception as e:
        if 'logger' in locals():
            logger.error(f"系统运行出错: {str(e)}")
            logger.error(traceback.format_exc())
        else:
            print(f"系统运行出错: {str(e)}")
            print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
