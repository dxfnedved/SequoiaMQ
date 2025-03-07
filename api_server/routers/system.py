"""
系统设置API路由

提供系统配置相关的功能，包括：
1. 获取系统信息
2. 查看日志
3. 管理缓存
"""

import os
import time
import json
import platform
import psutil
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from api_server.models import ResponseModel
from api_server.dependencies import get_logger_manager, get_workflow, get_data_fetcher
from logger_manager import LoggerManager
from data_fetcher import DataFetcher
import utils
import settings

# 创建路由
router = APIRouter(
    prefix="/system",
    tags=["系统设置"],
    responses={404: {"description": "未找到资源"}},
)

# 获取配置文件路径
CONFIG_FILE = "config.yaml"

class SystemInfo(BaseModel):
    """系统信息模型"""
    version: str = Field(default="1.0.0", description="系统版本")
    python_version: str = Field(description="Python版本")
    os_info: str = Field(description="操作系统信息")
    cpu_usage: float = Field(description="CPU使用率")
    memory_usage: float = Field(description="内存使用率")
    disk_usage: float = Field(description="磁盘使用率")
    uptime: float = Field(description="系统运行时间")
    available_cores: int = Field(description="可用CPU核心数")
    data_cache_size: float = Field(description="数据缓存大小(MB)")
    total_cached_stocks: int = Field(description="缓存的股票数量")

@router.get("/info", response_model=ResponseModel)
async def get_system_info(data_fetcher: DataFetcher = Depends(get_data_fetcher)):
    """获取系统信息"""
    # 获取系统信息
    cpu_usage = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # 获取数据缓存大小
    cache_size = 0
    cached_stocks = 0
    
    if os.path.exists(settings.STOCK_DATA_CACHE_DIR):
        for root, dirs, files in os.walk(settings.STOCK_DATA_CACHE_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    cache_size += os.path.getsize(file_path)
                    cached_stocks += 1
    
    # 构建系统信息
    info = {
        "version": "1.0.0",
        "python_version": platform.python_version(),
        "os_info": f"{platform.system()} {platform.release()}",
        "cpu_usage": cpu_usage,
        "memory_usage": memory.percent,
        "disk_usage": disk.percent,
        "uptime": time.time() - psutil.boot_time(),
        "available_cores": psutil.cpu_count(),
        "data_cache_size": round(cache_size / (1024 * 1024), 2),  # MB
        "total_cached_stocks": cached_stocks
    }
    
    return {
        "code": 200,
        "message": "获取系统信息成功",
        "data": info
    }

@router.get("/logs", response_model=ResponseModel)
async def get_logs(
    lines: int = Query(100, description="获取日志的行数", ge=1, le=1000),
    level: str = Query(None, description="日志级别过滤")
):
    """获取系统日志"""
    log_dir = "logs"
    log_files = []
    
    if os.path.exists(log_dir):
        for file in os.listdir(log_dir):
            if file.endswith(".log"):
                log_path = os.path.join(log_dir, file)
                log_files.append({
                    "file": file,
                    "size": os.path.getsize(log_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(log_path)).isoformat(),
                    "path": log_path
                })
    
    # 按修改时间排序
    log_files.sort(key=lambda x: x["modified"], reverse=True)
    
    logs = []
    if log_files:
        # 读取最新的日志文件
        latest_log = log_files[0]["path"]
        try:
            log_content = []
            with open(latest_log, "r", encoding="utf-8") as f:
                for line in f:
                    if level:
                        # 简单的日志级别过滤，实际应用中可能需要更复杂的解析
                        if f"[{level.upper()}]" in line:
                            log_content.append(line.strip())
                    else:
                        log_content.append(line.strip())
            
            # 获取最后指定行数
            logs = log_content[-lines:] if len(log_content) > lines else log_content
            
        except Exception as e:
            return {
                "code": 500,
                "message": f"读取日志文件失败: {str(e)}",
                "data": None
            }
    
    return {
        "code": 200,
        "message": "获取系统日志成功",
        "data": {
            "logs": logs,
            "log_files": log_files
        }
    }

@router.delete("/cache", response_model=ResponseModel)
async def clear_cache(
    cache_type: str = Query("stock", description="要清除的缓存类型: stock, analysis, all")
):
    """清除系统缓存"""
    cleared = []
    size_cleared = 0
    
    try:
        if cache_type in ["stock", "all"]:
            # 清除股票数据缓存
            if os.path.exists(settings.STOCK_DATA_CACHE_DIR):
                size = 0
                for file in os.listdir(settings.STOCK_DATA_CACHE_DIR):
                    file_path = os.path.join(settings.STOCK_DATA_CACHE_DIR, file)
                    if os.path.isfile(file_path):
                        size += os.path.getsize(file_path)
                        os.remove(file_path)
                
                cleared.append("stock_data")
                size_cleared += size
        
        if cache_type in ["analysis", "all"]:
            # 清除分析结果缓存
            if os.path.exists(settings.ANALYSIS_CACHE_DIR):
                size = 0
                for file in os.listdir(settings.ANALYSIS_CACHE_DIR):
                    file_path = os.path.join(settings.ANALYSIS_CACHE_DIR, file)
                    if os.path.isfile(file_path):
                        size += os.path.getsize(file_path)
                        os.remove(file_path)
                
                cleared.append("analysis_results")
                size_cleared += size
        
        return {
            "code": 200,
            "message": "缓存清除成功",
            "data": {
                "cleared_caches": cleared,
                "size_cleared_mb": round(size_cleared / (1024 * 1024), 2)
            }
        }
    
    except Exception as e:
        return {
            "code": 500,
            "message": f"清除缓存失败: {str(e)}",
            "data": None
        }

@router.get("/settings", response_model=ResponseModel)
async def get_settings():
    """获取系统设置"""
    # 读取配置文件
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            return {
                "code": 200,
                "message": "获取系统设置成功",
                "data": config
            }
        except Exception as e:
            return {
                "code": 500,
                "message": f"读取配置文件失败: {str(e)}",
                "data": None
            }
    else:
        # 返回默认设置
        default_settings = {
            "data_cache_duration": settings.CACHE_DURATION,
            "max_workers": settings.MAX_WORKERS,
            "retry_delay": settings.RETRY_DELAY,
            "max_retries": settings.MAX_RETRIES,
            "start_date": settings.START_DATE,
            "end_date": settings.END_DATE
        }
        
        return {
            "code": 200,
            "message": "获取系统默认设置成功",
            "data": default_settings
        }

@router.put("/settings", response_model=ResponseModel)
async def update_settings(settings_data: Dict[str, Any]):
    """更新系统设置"""
    # 确保配置目录存在
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    
    try:
        # 读取现有配置
        current_settings = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    current_settings = json.load(f)
            except:
                pass
        
        # 更新配置
        current_settings.update(settings_data)
        
        # 写入配置文件
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current_settings, f, ensure_ascii=False, indent=2)
        
        return {
            "code": 200,
            "message": "更新系统设置成功",
            "data": current_settings
        }
    
    except Exception as e:
        return {
            "code": 500,
            "message": f"更新系统设置失败: {str(e)}",
            "data": None
        }

@router.get("/status", response_model=ResponseModel)
async def check_system_status():
    """检查系统状态"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api_server": "running",
            "database": "running",
            "data_fetcher": "running"
        },
        "memory_usage": psutil.virtual_memory().percent,
        "cpu_usage": psutil.cpu_percent()
    }
    
    return {
        "code": 200,
        "message": "系统状态检查成功",
        "data": status
    } 