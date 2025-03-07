"""
用户管理路由

提供用户的CRUD接口
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from api_server.models import ResponseModel, User, UserCreate, UserUpdate
from api_server.dependencies import get_logger_manager
from api_server.database import (
    get_users, get_user_by_id, create_user, update_user, delete_user
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "User not found"}},
)

logger = get_logger_manager().get_logger("users_router")

@router.get("", response_model=ResponseModel)
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """
    获取用户列表，支持分页和搜索
    """
    try:
        result = get_users(page=page, page_size=page_size, search_term=search)
        return ResponseModel(code=200, message="获取用户列表成功", data=result)
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return ResponseModel(code=500, message=f"获取用户列表失败: {str(e)}")

@router.get("/{user_id}", response_model=ResponseModel)
async def get_user(user_id: int):
    """
    通过ID获取用户详情
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            return ResponseModel(code=404, message=f"用户 {user_id} 不存在")
        return ResponseModel(code=200, message="获取用户成功", data=user)
    except Exception as e:
        logger.error(f"获取用户失败: {str(e)}")
        return ResponseModel(code=500, message=f"获取用户失败: {str(e)}")

@router.post("", response_model=ResponseModel)
async def add_user(user: UserCreate):
    """
    创建新用户
    """
    try:
        user_dict = user.model_dump()
        new_user = create_user(user_dict)
        return ResponseModel(code=201, message="创建用户成功", data=new_user)
    except ValueError as ve:
        return ResponseModel(code=400, message=str(ve))
    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}")
        return ResponseModel(code=500, message=f"创建用户失败: {str(e)}")

@router.put("/{user_id}", response_model=ResponseModel)
async def modify_user(user_id: int, user: UserUpdate):
    """
    更新用户信息
    """
    try:
        user_dict = {k: v for k, v in user.model_dump().items() if v is not None}
        updated_user = update_user(user_id, user_dict)
        
        if not updated_user:
            return ResponseModel(code=404, message=f"用户 {user_id} 不存在")
            
        return ResponseModel(code=200, message="更新用户成功", data=updated_user)
    except ValueError as ve:
        return ResponseModel(code=400, message=str(ve))
    except Exception as e:
        logger.error(f"更新用户失败: {str(e)}")
        return ResponseModel(code=500, message=f"更新用户失败: {str(e)}")

@router.delete("/{user_id}", response_model=ResponseModel)
async def remove_user(user_id: int):
    """
    删除用户（软删除）
    """
    try:
        success = delete_user(user_id)
        if not success:
            return ResponseModel(code=404, message=f"用户 {user_id} 不存在")
            
        return ResponseModel(code=200, message="删除用户成功")
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        return ResponseModel(code=500, message=f"删除用户失败: {str(e)}") 