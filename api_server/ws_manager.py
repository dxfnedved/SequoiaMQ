"""
WebSocket管理器

这个模块管理WebSocket连接，用于实时推送分析和预测进度
"""

from typing import List, Dict, Any, Optional
from fastapi import WebSocket
import logging
import json
from datetime import datetime

class WebSocketManager:
    """WebSocket连接管理器"""
    
    # 活跃的WebSocket连接
    active_connections: List[WebSocket] = []
    
    @classmethod
    async def connect(cls, websocket: WebSocket):
        """建立WebSocket连接"""
        await websocket.accept()
        cls.active_connections.append(websocket)
        logging.info(f"WebSocket连接建立，当前连接数: {len(cls.active_connections)}")
    
    @classmethod
    def disconnect(cls, websocket: WebSocket):
        """关闭WebSocket连接"""
        if websocket in cls.active_connections:
            cls.active_connections.remove(websocket)
            logging.info(f"WebSocket连接关闭，当前连接数: {len(cls.active_connections)}")
    
    @classmethod
    async def broadcast_text(cls, message: str):
        """广播文本消息"""
        for connection in cls.active_connections.copy():
            try:
                await connection.send_text(message)
            except Exception as e:
                # 连接可能已关闭
                if connection in cls.active_connections:
                    cls.active_connections.remove(connection)
                logging.error(f"发送WebSocket消息失败: {str(e)}")
    
    @classmethod
    async def broadcast_json(cls, data: Dict[str, Any]):
        """广播JSON数据"""
        if not cls.active_connections:
            logging.warning("没有活跃的WebSocket连接，无法广播消息")
            return
            
        for connection in cls.active_connections.copy():
            try:
                await connection.send_json(data)
            except Exception as e:
                # 连接可能已关闭
                if connection in cls.active_connections:
                    cls.active_connections.remove(connection)
                logging.error(f"发送WebSocket JSON消息失败: {str(e)}")
    
    @classmethod
    async def broadcast_event(cls, event_type: str, data: Dict[str, Any]):
        """广播事件消息"""
        event_data = {
            "type": event_type,
            "data": data
        }
        await cls.broadcast_json(event_data)
    
    @classmethod
    async def broadcast_progress(cls, task_id: str, progress: float, status: str, message: Optional[str] = None):
        """广播进度更新事件"""
        progress_data = {
            "task_id": task_id,
            "progress": progress,
            "status": status
        }
        
        if message:
            progress_data["message"] = message
            
        await cls.broadcast_event("progress", progress_data)
    
    @classmethod
    def broadcast_json_sync(cls, data: Dict[str, Any]):
        """同步方式广播JSON数据"""
        # 在非异步环境中使用
        import asyncio
        
        # 获取或创建事件循环
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        # 如果当前有事件循环正在运行，则使用create_task
        if loop.is_running():
            asyncio.create_task(cls.broadcast_json(data))
        else:
            # 否则直接运行
            loop.run_until_complete(cls.broadcast_json(data)) 