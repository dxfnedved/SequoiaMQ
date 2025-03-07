"""
策略分析API路由

提供策略分析相关的功能，包括：
1. 启动分析任务
2. 获取分析结果
3. 管理分析配置
"""

import os
import json
import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from api_server.models import ResponseModel, AnalysisRequest, AnalysisResult, AnalysisTask, StrategyConfig
from api_server.dependencies import get_logger_manager, get_workflow, get_strategy_analyzer
from api_server.ws_manager import WebSocketManager
from work_flow import WorkFlow
from strategy_analyzer import StrategyAnalyzer
from utils import get_stock_info

# 创建路由
router = APIRouter(
    prefix="/analysis",
    tags=["策略分析"],
    responses={404: {"description": "未找到资源"}},
)

# 分析任务存储
analysis_tasks: Dict[str, AnalysisTask] = {}

# 分析结果缓存目录
ANALYSIS_CACHE_DIR = "cache/analysis"
os.makedirs(ANALYSIS_CACHE_DIR, exist_ok=True)

# WebSocket管理器
ws_manager = WebSocketManager()

def get_analysis_results_file():
    """获取最新的分析结果文件"""
    result_files = [f for f in os.listdir(ANALYSIS_CACHE_DIR) if f.endswith('.json')]
    if not result_files:
        return None
    
    # 按文件修改时间排序，返回最新的文件
    result_files.sort(key=lambda f: os.path.getmtime(os.path.join(ANALYSIS_CACHE_DIR, f)), reverse=True)
    return os.path.join(ANALYSIS_CACHE_DIR, result_files[0])

def read_analysis_results() -> List[Dict[str, Any]]:
    """读取分析结果"""
    results_file = get_analysis_results_file()
    if not results_file or not os.path.exists(results_file):
        return []
    
    try:
        with open(results_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def write_analysis_results(results: List[Dict[str, Any]]):
    """写入分析结果"""
    filename = f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(ANALYSIS_CACHE_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return filepath

def update_task_progress(task_id: str, progress: float, status: str = None, message: str = None):
    """更新任务进度并通过WebSocket广播"""
    if task_id in analysis_tasks:
        if progress is not None:
            analysis_tasks[task_id].progress = progress
        
        if status:
            analysis_tasks[task_id].status = status
            
        # 通过WebSocket广播进度
        ws_manager.broadcast_progress(task_id, progress, status or analysis_tasks[task_id].status, message)

async def run_analysis_task(
    task_id: str, 
    stocks: List[Any], 
    config: Optional[StrategyConfig],
    workflow: WorkFlow,
    strategy_analyzer: StrategyAnalyzer
):
    """运行分析任务"""
    try:
        # 更新任务状态
        update_task_progress(task_id, 0.0, "running", "正在初始化分析任务...")
        
        # 设置策略配置
        if config and config.enabledStrategies:
            # 应用策略启用/禁用设置
            all_strategies = list(strategy_analyzer.strategies.keys())
            for strategy_name in all_strategies:
                strategy_analyzer.strategies[strategy_name].enabled = strategy_name in config.enabledStrategies
                
            # 应用策略优先级
            if config.priorities:
                for strategy_name, priority in config.priorities.items():
                    if strategy_name in strategy_analyzer.strategy_priorities:
                        strategy_analyzer.strategy_priorities[strategy_name] = priority
        
        # 转换股票列表为标准格式
        stock_list = []
        if stocks:
            for stock in stocks:
                if isinstance(stock, dict):
                    stock_list.append(stock)
                elif isinstance(stock, str):
                    stock_list.append({"code": stock})
        else:
            # 如果没有指定股票，获取所有A股
            update_task_progress(task_id, 0.1, "running", "正在获取股票列表...")
            stock_list = get_stock_info()
            
        total_stocks = len(stock_list)
        analysis_tasks[task_id].total_stocks = total_stocks
        update_task_progress(task_id, 0.2, "running", f"准备分析 {total_stocks} 只股票...")
        
        # 开始分析
        results = []
        processed_count = 0
        
        for i, stock in enumerate(stock_list):
            try:
                update_task_progress(
                    task_id, 
                    0.2 + 0.7 * (i / total_stocks), 
                    "running", 
                    f"正在分析 {stock.get('code', stock)} ({i+1}/{total_stocks})..."
                )
                
                # 分析股票
                result = workflow.process_stock_data(stock)
                if result:
                    results.append(result)
                
                # 更新处理计数
                processed_count += 1
                analysis_tasks[task_id].processed_stocks = processed_count
                
            except Exception as e:
                print(f"分析股票 {stock} 出错: {str(e)}")
                continue
        
        # 保存结果
        update_task_progress(task_id, 0.95, "running", "正在保存分析结果...")
        results_file = write_analysis_results(results)
        
        # 完成任务
        update_task_progress(task_id, 1.0, "completed", "分析任务完成")
        
        return results
        
    except Exception as e:
        print(f"分析任务异常: {str(e)}")
        update_task_progress(task_id, 0.0, "error", f"分析任务出错: {str(e)}")
        raise

@router.get("", response_model=ResponseModel)
async def get_analysis_results():
    """获取分析结果"""
    results = read_analysis_results()
    return {
        "code": 200,
        "message": "获取分析结果成功",
        "data": results
    }

@router.post("/run", response_model=ResponseModel)
async def run_analysis(
    request: AnalysisRequest, 
    background_tasks: BackgroundTasks,
    workflow: WorkFlow = Depends(get_workflow),
    strategy_analyzer: StrategyAnalyzer = Depends(get_strategy_analyzer)
):
    """启动分析任务"""
    # 创建任务ID
    task_id = str(uuid.uuid4())
    
    # 创建任务记录
    task = AnalysisTask(
        task_id=task_id,
        start_time=datetime.now(),
        status="pending",
        progress=0.0,
        total_stocks=0,
        processed_stocks=0
    )
    
    # 保存任务
    analysis_tasks[task_id] = task
    
    # 在后台运行分析
    background_tasks.add_task(
        run_analysis_task,
        task_id,
        request.stocks,
        request.config,
        workflow,
        strategy_analyzer
    )
    
    return {
        "code": 200,
        "message": "分析任务已启动",
        "data": {
            "taskId": task_id,
            "startTime": task.start_time.isoformat(),
            "status": task.status
        }
    }

@router.get("/status/{task_id}", response_model=ResponseModel)
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in analysis_tasks:
        return {
            "code": 404,
            "message": f"任务 {task_id} 不存在",
            "data": None
        }
    
    task = analysis_tasks[task_id]
    
    return {
        "code": 200,
        "message": "获取任务状态成功",
        "data": {
            "taskId": task.task_id,
            "startTime": task.start_time.isoformat(),
            "status": task.status,
            "progress": task.progress,
            "totalStocks": task.total_stocks,
            "processedStocks": task.processed_stocks
        }
    }

@router.delete("/tasks/{task_id}", response_model=ResponseModel)
async def cancel_task(task_id: str):
    """取消分析任务"""
    if task_id not in analysis_tasks:
        return {
            "code": 404,
            "message": f"任务 {task_id} 不存在",
            "data": None
        }
    
    # 在实际应用中应该添加任务取消逻辑
    # 这里暂时只更新状态
    analysis_tasks[task_id].status = "cancelled"
    
    return {
        "code": 200,
        "message": f"任务 {task_id} 已取消",
        "data": None
    }

@router.get("/tasks", response_model=ResponseModel)
async def get_all_tasks():
    """获取所有任务"""
    tasks_data = []
    for task_id, task in analysis_tasks.items():
        tasks_data.append({
            "taskId": task.task_id,
            "startTime": task.start_time.isoformat(),
            "status": task.status,
            "progress": task.progress,
            "totalStocks": task.total_stocks,
            "processedStocks": task.processed_stocks
        })
    
    return {
        "code": 200,
        "message": "获取所有任务成功",
        "data": tasks_data
    }

@router.get("/strategies", response_model=ResponseModel)
async def get_available_strategies(strategy_analyzer: StrategyAnalyzer = Depends(get_strategy_analyzer)):
    """获取可用的策略列表"""
    strategies = []
    
    for name, strategy in strategy_analyzer.strategies.items():
        strategies.append({
            "name": name,
            "displayName": getattr(strategy, "display_name", name),
            "description": getattr(strategy, "description", ""),
            "enabled": getattr(strategy, "enabled", True),
            "priority": strategy_analyzer.strategy_priorities.get(name, 99)
        })
    
    return {
        "code": 200,
        "message": "获取策略列表成功",
        "data": strategies
    }

@router.get("/result/{code}", response_model=ResponseModel)
async def get_stock_analysis(
    code: str,
    workflow: WorkFlow = Depends(get_workflow)
):
    """获取特定股票的分析结果"""
    try:
        # 分析股票
        result = workflow.process_stock_data(code)
        
        return {
            "code": 200,
            "message": f"股票 {code} 分析成功",
            "data": result
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"分析错误: {str(e)}",
            "data": None
        } 