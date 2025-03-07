"""
股票数据API路由模块

提供股票相关的API端点
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
import traceback
import logging
from datetime import datetime

from api_server.dependencies import get_data_fetcher, get_logger_manager
from api_server.models import ResponseModel, ErrorModel, StockSearchItem, StockInfo, StockKline, StockPrice, CompanyInfo, StockFinancials
from data_fetcher import DataFetcher
from api_server.database import get_stocks_from_db, get_stock_by_code
from api_server.utils import get_stock_klines, get_stock_current_price, get_stock_history_price, get_stock_data, get_stock_financials, get_company_info, get_industry_stocks, get_industries, get_market_overview, get_holidays

# 创建股票路由
router = APIRouter(prefix="/stocks", tags=["stocks"])
logger = logging.getLogger(__name__)

# 定义请求和响应模�?
class StockInfoResponse(BaseModel):
    code: str
    name: str
    exchange: Optional[str] = None
    industry: Optional[str] = None
    
class StockPriceResponse(BaseModel):
    code: str
    name: Optional[str] = None
    price: float
    change: float
    changePercent: float
    open: float
    high: float
    low: float
    volume: int
    date: str
    
class StockHistoryRequest(BaseModel):
    code: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    period: Optional[str] = "daily"

class StockSearchRequest(BaseModel):
    keyword: str
    limit: Optional[int] = 10
    
# API端点实现
@router.get("/list", response_model=ResponseModel)
async def get_stock_list(
    data_fetcher: DataFetcher = Depends(get_data_fetcher),
    limit: int = Query(200, description="返回的股票数量限�?)
):
    """获取股票列表"""
    try:
        # 使用Utils中的函数获取股票列表
        from api_server.utils import get_stock_info
        stocks = get_stock_info()
        if limit and limit > 0:
            stocks = stocks[:limit]
        
        return {
            "success": True,
            "data": stocks,
            "message": "获取股票列表成功"
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"获取股票列表失败: {str(e)}"
        }
        
@router.get("/search", response_model=List[StockSearchItem])
async def search_stocks(keyword: str = Query(..., description="股票代码或名称关键词")):
    """
    搜索股票
    """
    try:
        if not keyword or len(keyword.strip()) == 0:
            return []
            
        # 使用数据库搜索股�?
        stocks = get_stocks_from_db(keyword, limit=10)
        
        if not stocks:
            logger.info(f"股票搜索 '{keyword}' 未找到结�?)
            return []
            
        results = []
        for stock in stocks:
            results.append(StockSearchItem(
                code=stock["code"],
                name=stock["name"],
                market=stock.get("market", ""),
                industry=stock.get("industry", "")
            ))
            
        logger.info(f"股票搜索 '{keyword}' 找到 {len(results)} 个结�?)
        return results
            
    except Exception as e:
        logger.error(f"搜索股票时发生错�? {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"搜索股票时发生错�? {str(e)}")
        
@router.get("/info/{code}", response_model=StockInfo)
async def get_stock_info(code: str):
    """
    获取股票基本信息
    """
    try:
        # 先从数据库获取股票基本信�?
        stock = get_stock_by_code(code)
        
        if not stock:
            logger.error(f"未找到股�?{code} 的基本信�?)
            raise HTTPException(status_code=404, detail=f"未找到股�?{code} 的基本信�?)
            
        # 获取股票最新价�?
        price_data = await get_stock_current_price(code)
        
        # 整合数据
        stock_info = StockInfo(
            code=stock["code"],
            name=stock["name"],
            market=stock.get("market", ""),
            price=price_data.get("price", 0),
            change=price_data.get("change", 0),
            change_percent=price_data.get("change_percent", 0),
            volume=price_data.get("volume", 0),
            amount=price_data.get("amount", 0),
            industry=stock.get("industry", ""),
            update_time=datetime.now().isoformat()
        )
        
        return stock_info
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票信息时发生错�? {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"获取股票信息时发生错�? {str(e)}")
        
@router.get("/{code}", response_model=ResponseModel)
async def get_stock_detail(
    code: str,
    data_fetcher: DataFetcher = Depends(get_data_fetcher)
):
    """获取股票详情"""
    try:
        # 获取当前股票价格
        stock_data = await data_fetcher.get_stock_data(code)
        if not stock_data or stock_data.empty:
            raise HTTPException(status_code=404, detail=f"未找到股票代�?{code} 的数�?)
            
        # 获取最新的一条记�?
        latest = stock_data.iloc[-1]
        
        # 获取股票基本信息
        from api_server.utils import get_stock_info
        all_stocks = get_stock_info()
        stock_info = next((s for s in all_stocks if s['code'] == code), {"name": "未知", "code": code})
        
        # 计算涨跌�?
        prev_close = stock_data.iloc[-2]['close'] if len(stock_data) > 1 else latest['open']
        change = latest['close'] - prev_close
        change_percent = (change / prev_close * 100) if prev_close != 0 else 0
        
        result = {
            "code": code,
            "name": stock_info.get("name", "未知"),
            "price": float(latest['close']),
            "change": float(change),
            "changePercent": float(change_percent),
            "open": float(latest['open']),
            "high": float(latest['high']),
            "low": float(latest['low']),
            "volume": int(latest['volume']),
            "date": latest.name.strftime("%Y-%m-%d") if hasattr(latest.name, "strftime") else str(latest.name)
        }
            
        return {
            "success": True,
            "data": result,
            "message": "获取股票详情成功"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"获取股票详情失败: {str(e)}"
        }
        
@router.get("/{code}/history", response_model=ResponseModel)
async def get_stock_history(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: str = "daily",
    data_fetcher: DataFetcher = Depends(get_data_fetcher)
):
    """获取股票历史数据"""
    try:
        # 获取历史数据
        stock_data = await data_fetcher.get_stock_data(code, start_date=start_date, end_date=end_date, period=period)
        if stock_data.empty:
            raise HTTPException(status_code=404, detail=f"未找到股票代�?{code} 的历史数�?)
            
        # 转换为列表形�?
        history = []
        for idx, row in stock_data.iterrows():
            history.append({
                "date": idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": int(row['volume'])
            })
            
        return {
            "success": True,
            "data": history,
            "message": "获取股票历史数据成功"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"获取股票历史数据失败: {str(e)}"
        } 
