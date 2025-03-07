"""
自选股管理API路由

提供自选股的增删改查功能
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from api_server.models import ResponseModel, StockBase, WatchlistItem, AddToWatchlistRequest, StockDetail
from api_server.dependencies import get_logger_manager, get_data_fetcher
from api_server.database import get_watchlist, add_to_watchlist, remove_from_watchlist, update_watchlist_item, clear_watchlist
from data_fetcher import DataFetcher

# 创建路由
router = APIRouter(
    prefix="/watchlist",
    tags=["自选股管理"],
    responses={404: {"description": "未找到资源"}},
)

@router.get("", response_model=ResponseModel)
async def get_watchlist_api():
    """获取自选股列表"""
    try:
        watchlist = get_watchlist()
        return {
            "code": 200,
            "message": "获取自选股列表成功",
            "data": watchlist
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取自选股失败: {str(e)}")

@router.post("", response_model=ResponseModel)
async def add_to_watchlist_api(stock: AddToWatchlistRequest, data_fetcher: DataFetcher = Depends(get_data_fetcher)):
    """添加股票到自选股"""
    try:
        # 检查股票是否已经在自选股中
        existing_watchlist = get_watchlist()
        if any(item["code"] == stock.code for item in existing_watchlist):
            return {
                "code": 400,
                "message": f"股票 {stock.code} 已经在自选股列表中",
                "data": None
            }
        
        # 确保有股票名称
        name = stock.name
        if not name:
            # 尝试获取股票名称
            try:
                all_stocks = data_fetcher.get_stock_list()
                stock_info = next((s for s in all_stocks if s['code'] == stock.code), None)
                if stock_info:
                    name = stock_info.get('name', '')
            except Exception as e:
                # 如果获取失败，忽略错误
                pass
        
        # 创建新的自选股项目
        new_item = {
            "code": stock.code,
            "name": name or "未知",
            "add_time": datetime.now().isoformat(),
            "notes": stock.notes or ""
        }
        
        # 添加到数据库
        result = add_to_watchlist(new_item)
        
        return {
            "code": 200,
            "message": f"股票 {stock.code} 添加到自选股成功",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加自选股失败: {str(e)}")

@router.delete("/{code}", response_model=ResponseModel)
async def remove_from_watchlist_api(code: str):
    """从自选股移除股票"""
    try:
        # 从数据库中删除
        removed_item = remove_from_watchlist(code)
        
        if not removed_item:
            return {
                "code": 404,
                "message": f"股票 {code} 不在自选股列表中",
                "data": None
            }
        
        return {
            "code": 200,
            "message": f"股票 {code} 从自选股中移除成功",
            "data": removed_item
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除自选股失败: {str(e)}")

@router.put("/{code}", response_model=ResponseModel)
async def update_watchlist_item_api(code: str, data: Dict[str, Any]):
    """更新自选股项目"""
    try:
        # 更新数据库中的项目
        updated_item = update_watchlist_item(code, data)
        
        if not updated_item:
            return {
                "code": 404,
                "message": f"股票 {code} 不在自选股列表中",
                "data": None
            }
        
        return {
            "code": 200,
            "message": f"股票 {code} 信息更新成功",
            "data": updated_item
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新自选股失败: {str(e)}")

@router.delete("", response_model=ResponseModel)
async def clear_watchlist_api():
    """清空自选股列表"""
    try:
        deleted_count = clear_watchlist()
        
        return {
            "code": 200,
            "message": f"自选股列表已清空，共删除{deleted_count}条记录",
            "data": None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空自选股失败: {str(e)}")

@router.get("/details", response_model=ResponseModel)
async def get_watchlist_details(data_fetcher: DataFetcher = Depends(get_data_fetcher)):
    """获取自选股详细信息（包括实时价格等）"""
    try:
        watchlist = get_watchlist()
        
        if not watchlist:
            return {
                "code": 200,
                "message": "自选股列表为空",
                "data": []
            }
        
        # 为每个股票添加实时数据
        detailed_watchlist = []
        for item in watchlist:
            code = item["code"]
            try:
                # 获取股票数据
                stock_data = data_fetcher.get_stock_data(code)
                
                if stock_data is not None and not stock_data.empty:
                    # 获取最新一条记录
                    latest = stock_data.iloc[-1]
                    
                    # 创建详细信息
                    detailed_item = {
                        **item,
                        "price": float(latest["close"]),
                        "price_change": float(latest["close"] / latest["open"] - 1),
                        "volume": float(latest["volume"]),
                        "last_update": datetime.now().isoformat()
                    }
                else:
                    detailed_item = item
                    
                detailed_watchlist.append(detailed_item)
            except Exception as e:
                # 如果获取失败，使用原始数据
                detailed_watchlist.append(item)
        
        return {
            "code": 200,
            "message": "获取自选股详细信息成功",
            "data": detailed_watchlist
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取自选股详情失败: {str(e)}") 