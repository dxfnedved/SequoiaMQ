# -*- encoding: UTF-8 -*-
import yaml
import os
from logger_manager import LoggerManager

logger = LoggerManager().get_logger("settings")

def init():
    """初始化配置"""
    global config
    
    try:
        # 加载配置文件
        root_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(root_dir, 'config.yaml')
        
        if not os.path.exists(config_file):
            # 创建默认配置
            config = {
                'cron': False,
                'data_dir': 'data',
                'cache_dir': 'cache',
                'log_level': 'INFO',
                'batch_size': 100,  # 批量处理时的每批大小
                'analysis': {
                    'use_cache': True,
                    'cache_days': 1,
                    'parallel': True,
                    'max_workers': 4
                }
            }
            
            # 保存默认配置
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)
            logger.info("创建默认配置文件")
        else:
            # 读取现有配置
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info("加载配置文件成功")
            
        # 创建必要的目录
        for dir_name in ['data_dir', 'cache_dir']:
            if dir_name in config:
                os.makedirs(config[dir_name], exist_ok=True)
                
        return config
        
    except Exception as e:
        logger.error(f"初始化配置失败: {str(e)}")
        raise

def get_config():
    """获取配置"""
    global config
    if not 'config' in globals():
        config = init()
    return config