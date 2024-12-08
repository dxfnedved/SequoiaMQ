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
        self.log_dir = os.path.join(base_dir, 'logs', self.date, self.timestamp)
        self.result_dir = os.path.join(base_dir, 'results', self.date, self.timestamp)
        
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
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 创建控制台处理器（INFO级别）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 创建主日志文件处理器（INFO级别）
        main_log_file = os.path.join(self.log_dir, "main.log")
        file_handler = logging.FileHandler(main_log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # 创建调试日志文件处理器（DEBUG级别）
        debug_log_file = os.path.join(self.log_dir, "debug.log")
        debug_handler = logging.FileHandler(debug_log_file, encoding='utf-8')
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        root_logger.addHandler(debug_handler)
        
        # 设置loguru
        logger.remove()  # 移除默认处理器
        
        # 添加loguru控制台处理器
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO",
            colorize=True
        )
        
        # 添加loguru文件处理器
        logger.add(
            os.path.join(self.log_dir, "loguru.log"),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="1 day",
            encoding="utf-8"
        )
        
        # 为每个模块创建单独的日志记录器
        self.setup_module_loggers()
    
    def setup_module_loggers(self):
        """为所有模块设置日志记录器"""
        modules = {
            'data_fetcher': 'loguru',
            'work_flow': 'logging',
            'stock_selector': 'logging',
            'stock_chart': 'loguru',
            'strategy': 'logging'
        }
        
        for module_name, logger_type in modules.items():
            if logger_type == 'logging':
                self.setup_logging_logger(module_name)
            else:
                self.setup_loguru_logger(module_name)
    
    def setup_logging_logger(self, module_name):
        """设置logging类型的日志记录器"""
        logger = logging.getLogger(module_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False  # 避免日志重复
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 创建文件处理器
        log_file = os.path.join(self.log_dir, f"{module_name}.log")
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    def setup_loguru_logger(self, module_name):
        """设置loguru类型的日志记录器"""
        logger.add(
            os.path.join(self.log_dir, f"{module_name}.log"),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            filter=lambda record: record["extra"].get("name") == module_name,
            level="DEBUG",
            rotation="1 day",
            encoding="utf-8"
        )
    
    def get_logger(self, name):
        """获取指定模块的日志记录器"""
        if name in ['data_fetcher', 'stock_chart']:
            return logger.bind(name=name)
        else:
            return logging.getLogger(name)
    
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