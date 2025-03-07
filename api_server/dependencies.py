"""
依赖项管理

这个模块定义了FastAPI路由处理器依赖的对象，使用依赖注入模式简化对象获取
"""

from work_flow import WorkFlow
from logger_manager import LoggerManager
from data_fetcher import DataFetcher
from strategy_analyzer import StrategyAnalyzer
from datetime import datetime
import os
import sys
from typing import Optional

# 将项目根目录添加到sys.path
api_server_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(api_server_path)
sys.path.append(project_root)

# 尝试导入LLM_PREDICT相关模块
try:
    from LLM_PREDICT.llm_interface import LLMInterface
    from LLM_PREDICT.workflow_manager import WorkflowManager as LLMWorkflowManager
    llm_modules_available = True
except ImportError as e:
    print(f"警告: 无法导入LLM_PREDICT模块: {e}")
    llm_modules_available = False

# 导入项目模块
from api_server.database import get_db_connection, init_db

# 单例对象
_logger_manager = None
_data_fetcher = None
_workflow = None
_strategy_analyzer = None
_llm_interface = None
_llm_workflow_manager = None

def get_logger_manager():
    """获取日志管理器实例（单例模式）"""
    global _logger_manager
    if _logger_manager is None:
        # 创建日志管理器
        _logger_manager = LoggerManager(
            base_dir=project_root
        )
    return _logger_manager

def get_data_fetcher():
    """获取数据获取器实例（单例模式）"""
    global _data_fetcher
    if _data_fetcher is None:
        _data_fetcher = DataFetcher(logger_manager=get_logger_manager())
    return _data_fetcher

def get_strategy_analyzer():
    """获取策略分析器实例（单例模式）"""
    global _strategy_analyzer
    if _strategy_analyzer is None:
        _strategy_analyzer = StrategyAnalyzer(logger_manager=get_logger_manager())
    return _strategy_analyzer

def get_workflow():
    """获取工作流实例（单例模式）"""
    global _workflow
    if _workflow is None:
        _workflow = WorkFlow(logger_manager=get_logger_manager())
    return _workflow

def get_llm_interface():
    """获取LLM接口实例（单例模式）"""
    global _llm_interface
    if _llm_interface is None and llm_modules_available:
        try:
            _llm_interface = LLMInterface()
        except Exception as e:
            print(f"创建LLM接口失败: {e}")
            return None
    return _llm_interface

def get_llm_workflow_manager():
    """获取LLM工作流管理器实例（单例模式）"""
    global _llm_workflow_manager
    if _llm_workflow_manager is None and llm_modules_available:
        try:
            _llm_workflow_manager = LLMWorkflowManager()
        except Exception as e:
            print(f"创建LLM工作流管理器失败: {e}")
            return None
    return _llm_workflow_manager

def get_db() -> get_db_connection:
    """获取数据库连接"""
    db = get_db_connection()
    try:
        yield db
    finally:
        db.close()

# 确保应用启动时数据库已初始化
init_db() 