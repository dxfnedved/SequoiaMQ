# -*- encoding: UTF-8 -*-
import os
from logger_manager import LoggerManager
import json
from pathlib import Path
import logging
import traceback
from datetime import datetime
logger = LoggerManager().get_logger("settings")

# Base directories
BASE_CACHE_DIR = 'cache'

# Cache subdirectories
STOCK_DATA_CACHE_DIR = os.path.join(BASE_CACHE_DIR, 'stock_data')
STOCK_LIST_CACHE_DIR = os.path.join(BASE_CACHE_DIR, 'stock_list')
ANALYSIS_CACHE_DIR = os.path.join(BASE_CACHE_DIR, 'analysis')
NEWS_CACHE_DIR = os.path.join(BASE_CACHE_DIR, 'news')

# Cache settings
CACHE_DURATION = 24 * 60 * 60  # 24 hours in seconds
MAX_RETRIES = 3
RETRY_DELAY = 2
START_DATE = '20240101'
END_DATE = datetime.now().strftime('%Y%m%d')

# Ensure cache directories exist
for cache_dir in [STOCK_DATA_CACHE_DIR, STOCK_LIST_CACHE_DIR, ANALYSIS_CACHE_DIR, NEWS_CACHE_DIR]:
    os.makedirs(cache_dir, exist_ok=True)

def init():
    """初始化配置"""
    try:
        # 获取配置文件路径
        config_file = 'config.json'
        
        # 如果配置文件不存在，创建默认配置
        if not os.path.exists(config_file):
            default_config = {
                'data_dir': 'data',
                'cache_dir': 'cache',
                'log_dir': 'logs',
                'summary_dir': 'summary',
                'data_update_interval': 3600,  # 数据更新间隔（秒）
                'cache_expire_time': 86400,    # 缓存过期时间（秒）
                'request_interval': 1,         # 请求间隔（秒）
                'max_retries': 3,             # 最大重试次数
                'retry_delay': 2,             # 重试延迟（秒）
                'batch_size': 50,             # 批处理大小
                'batch_delay': 1,             # 批处理间隔（秒）
                'max_processes': 4,           # 最大进程数
                'log_level': 'INFO',
                'data_quality': {
                    'min_days': 20,           # 最小数据天数
                    'max_missing_ratio': 0.2,  # 最大缺失比例
                    'max_gap_days': 5         # 最大数据间隔天数
                }
            }
            
            # 创���配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
                
            logging.info(f"创建默认配置文件: {config_file}")
            
        # 读取配置
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 创建必要的目录
        for dir_name in [config['data_dir'], config['cache_dir'], 
                        config['log_dir'], config['summary_dir']]:
            os.makedirs(dir_name, exist_ok=True)
            
        # 设置日志级别
        logging.basicConfig(
            level=getattr(logging, config['log_level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logging.info("配置加载完成")
        return config
        
    except Exception as e:
        logging.error(f"初始化配置失败: {str(e)}")
        logging.error(traceback.format_exc())
        raise

def get_config():
    """获取配置"""
    global config
    if not 'config' in globals():
        config = init()
    return config