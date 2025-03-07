import os
from datetime import datetime
import sys
import logging
from loguru import logger

class LoggerManager:
    """日志管理器"""
    
    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.date = datetime.now().strftime('%Y%m%d')
        
        # 创建日志目录结构
        self.log_dir = os.path.join(base_dir, 'logs', self.date)
        self.result_dir = os.path.join(base_dir, 'results', self.date)
        
        # 创建必要的目录
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.result_dir, exist_ok=True)
        
        # 初始化日志记录器
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志系统"""
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # 清除现有的处理器
        root_logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # 创建控制台处理器（只显示ERROR和关键INFO）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(self.filter_console_logs)
        root_logger.addHandler(console_handler)
        
        # 创建主日志文件处理器（ERROR和关键INFO）
        main_log_file = os.path.join(self.log_dir, "main.log")
        file_handler = logging.FileHandler(main_log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(self.filter_main_logs)
        root_logger.addHandler(file_handler)
        
        # 创建调试日志文件处理器（所有DEBUG信息）
        debug_log_file = os.path.join(self.log_dir, "debug.log")
        debug_handler = logging.FileHandler(debug_log_file, encoding='utf-8')
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        root_logger.addHandler(debug_handler)
        
    def filter_console_logs(self, record):
        """过滤控制台日志"""
        # 始终显示错误和警告
        if record.levelno >= logging.WARNING:
            return True
            
        # 显示大多数INFO消息
        if record.levelno == logging.INFO:
            # 排除一些不重要的INFO消息
            exclude_messages = [
                "debug",
                "trace",
                "详细信息"
            ]
            return not any(msg in record.msg.lower() for msg in exclude_messages)
            
        return False
        
    def filter_main_logs(self, record):
        """过滤主日志文件内容"""
        # 记录所有错误和警告
        if record.levelno >= logging.WARNING:
            return True
            
        # 记录大多数INFO消息
        if record.levelno == logging.INFO:
            return True
            
        return False
        
    def setup_module_loggers(self):
        """为所有模块设置日志记录器"""
        modules = {
            'data_fetcher': logging.DEBUG,
            'work_flow': logging.INFO,
            'stock_selector': logging.INFO,
            'stock_chart': logging.DEBUG,
            'strategy': logging.DEBUG
        }
        
        for module_name, level in modules.items():
            self.setup_module_logger(module_name, level)
    
    def setup_module_logger(self, module_name, level):
        """设置模块日志记录器"""
        logger = logging.getLogger(module_name)
        logger.setLevel(level)
        logger.propagate = False  # 避免日志重复
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # 创建文件处理器
        log_file = os.path.join(self.log_dir, f"{module_name}.log")
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setLevel(level)
        handler.setFormatter(formatter)
        
        # 添加过滤器
        if module_name == 'work_flow':
            handler.addFilter(self.filter_main_logs)
            
        logger.addHandler(handler)
        
        # 如果是work_flow模块，添加控制台处理器
        if module_name == 'work_flow':
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            console_handler.addFilter(self.filter_console_logs)
            logger.addHandler(console_handler)
    
    def get_logger(self, name, propagate=False):
        """获取指定模块的日志记录器"""
        logger = logging.getLogger(name)
        logger.propagate = propagate
        return logger
    
    def get_result_path(self, filename):
        """获取结果文件的完整路径"""
        return os.path.join(self.result_dir, filename)
    
    def get_log_path(self, filename):
        """获取日志文件的完整路径"""
        return os.path.join(self.log_dir, filename)
    
    def create_result_subdirectory(self, subdir):
        """创建结果子目录"""
        path = os.path.join(self.result_dir, subdir)
        os.makedirs(path, exist_ok=True)
        return path
    
    @property
    def current_timestamp(self):
        """获取当前时间戳"""
        return self.timestamp