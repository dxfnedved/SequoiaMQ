@router.get("/stocks/search", response_model=ResponseModel)
async def search_stocks(
    query: str = Query("", description="搜索关键词，支持股票代码或名称的模糊匹配"),
    limit: int = Query(10, description="返回结果数量限制", ge=1, le=100),
