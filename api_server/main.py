"""
SequoiaMQ API服务器

这个模块提供了SequoiaMQ的RESTful API接口，支持：
1. 自选股管理
2. 策略分析
3. 预测（LSTM/LLM）
4. 系统配置
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 将项目根目录添加到路径中，以便导入其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入现有的模块
from work_flow import WorkFlow
from logger_manager import LoggerManager
from data_fetcher import DataFetcher
from utils import get_stock_info

# 导入API服务器模块
from api_server.routers import watchlist, analysis, prediction, system, users, stocks
from api_server.dependencies import get_logger_manager, get_workflow, get_data_fetcher
from api_server.models import ResponseModel
from api_server.ws_manager import WebSocketManager

# 创建FastAPI应用实例
app = FastAPI(
    title="SequoiaMQ API",
    description="SequoiaMQ的API服务器，提供股票分析、预测和自选股管理功能",
    version="1.0.0"
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置为特定的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置日志
log_file = f'logs/api_server_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
os.makedirs('logs', exist_ok=True)
logger_manager = LoggerManager(log_file)
logger = logger_manager.get_logger("api_server")

# WebSocket管理器
ws_manager = WebSocketManager()

# 注册路由
app.include_router(watchlist.router)
app.include_router(analysis.router)
app.include_router(prediction.router)
app.include_router(system.router)
app.include_router(users.router)
app.include_router(stocks.router)

@app.get("/", response_model=ResponseModel)
async def root():
    """API根路径，返回基本信息"""
    return {
        "code": 200,
        "message": "SequoiaMQ API服务器已启动",
        "data": {
            "version": "1.0.0",
            "api_docs": "/docs",
            "timestamp": datetime.now().isoformat()
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接，用于实时推送分析和预测进度"""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 这里简单地将接收到的数据回显
            await websocket.send_json({"message": f"收到: {data}"})
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
    finally:
        await ws_manager.disconnect(websocket)

# 事件处理程序
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的操作"""
    logger.info("API服务器启动")
    # 确保必要的目录存在
    for dir_name in ['data', 'logs', 'cache', 'summary']:
        os.makedirs(dir_name, exist_ok=True)
        
    # 初始化数据库
    from api_server.database import init_db
    try:
        init_db()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行的操作"""
    logger.info("API服务器关闭")

# 启动服务器的入口点（如果直接运行此文件）
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 