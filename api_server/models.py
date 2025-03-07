"""
API数据模型定义

这个模块定义了API使用的数据模型（请求和响应），使用Pydantic
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

# 通用响应模型
class ResponseModel(BaseModel):
    """API通用响应模型"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[Any] = Field(default=None, description="响应数据")

# 股票基本模型
class StockBase(BaseModel):
    """股票基本信息模型"""
    code: str = Field(description="股票代码")
    name: Optional[str] = Field(default=None, description="股票名称")

class StockDetail(StockBase):
    """股票详细信息模型"""
    industry: Optional[str] = Field(default=None, description="所属行业")
    current_price: Optional[float] = Field(default=None, description="当前价格")
    change: Optional[float] = Field(default=None, description="涨跌幅")
    volume: Optional[float] = Field(default=None, description="成交量")
    last_update: Optional[datetime] = Field(default=None, description="最后更新时间")

# 自选股相关模型
class WatchlistItem(StockBase):
    """自选股项目模型"""
    add_time: Optional[datetime] = Field(default=None, description="添加时间")
    notes: Optional[str] = Field(default=None, description="备注")

class AddToWatchlistRequest(StockBase):
    """添加自选股请求模型"""
    notes: Optional[str] = Field(default=None, description="备注")

# 策略相关模型
class StrategyConfig(BaseModel):
    """策略配置模型"""
    enabledStrategies: List[str] = Field(default=[], description="启用的策略列表")
    priorities: Dict[str, int] = Field(default={}, description="策略优先级")
    useParallel: bool = Field(default=True, description="是否使用并行处理")
    maxWorkers: int = Field(default=8, description="最大并行工作线程数")

class AnalysisRequest(BaseModel):
    """分析请求模型"""
    stocks: Optional[List[Union[str, StockBase]]] = Field(default=None, description="要分析的股票列表，为空则分析所有股票")
    config: Optional[StrategyConfig] = Field(default=None, description="分析配置")

class SignalDetail(BaseModel):
    """信号详情模型"""
    strategy: str = Field(description="策略名称")
    type: str = Field(description="信号类型")
    factors: Dict[str, Any] = Field(default={}, description="因子数据")
    strength: float = Field(default=1.0, description="信号强度")
    execution_time: Optional[float] = Field(None, description="执行时间")

class AnalysisResult(StockBase):
    """分析结果模型"""
    buy_signals: int = Field(default=0, description="买入信号数量")
    sell_signals: int = Field(default=0, description="卖出信号数量")
    strategies: List[str] = Field(default=[], description="触发的策略")
    signal_details: List[SignalDetail] = Field(default=[], description="信号详情")
    data_date: Optional[str] = Field(default=None, description="数据日期")
    analysis_time: Optional[float] = Field(default=None, description="分析耗时")
    batch_id: Optional[str] = Field(default=None, description="批次ID")
    indicators: Optional[Dict[str, Any]] = Field(default=None, description="技术指标")

class AnalysisTask(BaseModel):
    """分析任务模型"""
    task_id: str = Field(description="任务ID")
    start_time: datetime = Field(description="开始时间")
    status: str = Field(default="running", description="任务状态")
    progress: float = Field(default=0.0, description="进度")
    total_stocks: int = Field(default=0, description="总股票数量")
    processed_stocks: int = Field(default=0, description="已处理股票数量")

# 预测相关模型
class LstmConfig(BaseModel):
    """LSTM配置模型"""
    timeSteps: int = Field(default=20, description="时间步长")
    epochs: int = Field(default=100, description="训练轮数")
    batchSize: int = Field(default=32, description="批处理大小")
    lookAhead: int = Field(default=5, description="预测天数")

class LlmConfig(BaseModel):
    """LLM配置模型"""
    includeTechnical: bool = Field(default=True, description="包含技术分析")
    includeNews: bool = Field(default=True, description="包含新闻分析")
    includeFinancial: bool = Field(default=True, description="包含财务分析")
    modelType: str = Field(default="gpt-4", description="LLM模型类型")

class PredictionRequest(BaseModel):
    """预测请求模型"""
    code: str = Field(description="股票代码")
    name: Optional[str] = Field(default=None, description="股票名称")
    config: Optional[Union[LstmConfig, LlmConfig]] = Field(default=None, description="预测配置")

class PredictionItem(BaseModel):
    """预测项目模型"""
    date: str = Field(description="日期")
    price: float = Field(description="预测价格")
    confidence: float = Field(description="置信度")

class PredictionMetrics(BaseModel):
    """预测指标模型"""
    mse: Optional[float] = Field(default=None, description="均方误差")
    accuracy: Optional[float] = Field(default=None, description="准确率")

class PredictionResult(BaseModel):
    """预测结果模型"""
    code: str = Field(description="股票代码")
    name: Optional[str] = Field(default=None, description="股票名称")
    date: str = Field(description="预测日期")
    type: str = Field(description="预测类型")
    predictions: List[PredictionItem] = Field(description="预测数据")
    metrics: Optional[PredictionMetrics] = Field(default=None, description="评价指标")

class PredictionTask(BaseModel):
    """预测任务模型"""
    task_id: str = Field(description="任务ID")
    code: str = Field(description="股票代码")
    start_time: datetime = Field(description="开始时间")
    type: str = Field(description="预测类型")
    status: str = Field(default="running", description="任务状态")
    progress: float = Field(default=0.0, description="进度")

# 用户相关模型
class User(BaseModel):
    """用户模型"""
    id: Optional[int] = Field(default=None, description="用户ID")
    name: str = Field(description="用户名称")
    avatar_url: Optional[str] = Field(default=None, description="头像URL")
    mobile: str = Field(description="手机号")
    energy_coin: int = Field(default=0, description="能量币")

class UserCreate(BaseModel):
    """创建用户请求模型"""
    name: str = Field(description="用户名称")
    avatar_url: Optional[str] = Field(default=None, description="头像URL")
    mobile: str = Field(description="手机号")

class UserUpdate(BaseModel):
    """更新用户请求模型"""
    name: Optional[str] = Field(default=None, description="用户名称")
    avatar_url: Optional[str] = Field(default=None, description="头像URL")
    mobile: Optional[str] = Field(default=None, description="手机号")
    energy_coin: Optional[int] = Field(default=None, description="能量币")

class UserModel(BaseModel):
    """用户模型"""
    id: Optional[int] = None
    username: str
    password: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    is_admin: bool = False
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class UserCreateModel(BaseModel):
    """用户创建模型"""
    username: str
    password: str
    email: Optional[str] = None
    is_admin: bool = False

class UserUpdateModel(BaseModel):
    """用户更新模型"""
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    is_admin: Optional[bool] = None

class LoginModel(BaseModel):
    """登录模型"""
    username: str
    password: str

class TokenModel(BaseModel):
    """令牌模型"""
    access_token: str
    token_type: str = "bearer"
    user: UserModel

class StockModel(BaseModel):
    """股票模型"""
    code: str
    name: str
    industry: Optional[str] = None
    market: Optional[str] = None

class WatchlistItemModel(BaseModel):
    """自选股项目模型"""
    id: Optional[int] = None
    code: str
    name: str
    industry: Optional[str] = None
    add_time: Optional[datetime] = None
    notes: Optional[str] = None
    
    class Config:
        orm_mode = True

class WatchlistItemCreateModel(BaseModel):
    """自选股项目创建模型"""
    code: str
    name: str
    industry: Optional[str] = None
    notes: Optional[str] = None

class WatchlistItemUpdateModel(BaseModel):
    """自选股项目更新模型"""
    name: Optional[str] = None
    industry: Optional[str] = None
    notes: Optional[str] = None

class AnalysisStrategyModel(BaseModel):
    """分析策略模型"""
    id: str
    name: str
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    enabled: bool = True

class AnalysisResultModel(BaseModel):
    """分析结果模型"""
    id: Optional[str] = None
    code: str
    name: str
    date: datetime
    passed: bool
    strategy_id: str
    strategy_name: str
    details: Optional[Dict[str, Any]] = None

class AnalysisTaskModel(BaseModel):
    """分析任务模型"""
    id: str
    status: str  # pending, running, completed, error
    progress: float
    start_time: datetime
    end_time: Optional[datetime] = None
    stocks: List[str]
    strategies: List[str]

class AnalysisRequestModel(BaseModel):
    """分析请求模型"""
    stocks: List[str]
    strategies: List[str]
    
# 预测相关模型

class LstmConfig(BaseModel):
    """LSTM配置模型"""
    lookBack: Optional[int] = 60  # 回溯时间步长
    epochs: Optional[int] = 100  # 训练轮数
    batchSize: Optional[int] = 64  # 批次大小
    units: Optional[int] = 50  # LSTM单元数量

class LlmConfig(BaseModel):
    """LLM配置模型"""
    includeTechnical: Optional[bool] = True  # 包含技术指标
    includeNews: Optional[bool] = True  # 包含新闻
    includeFinancial: Optional[bool] = False  # 包含财务数据
    modelType: Optional[str] = "deepseek-chat"  # 模型类型

class PredictionRequest(BaseModel):
    """预测请求模型"""
    stockCode: str  # 股票代码
    stockName: Optional[str] = None  # 股票名称
    days: Optional[int] = 5  # 预测天数
    config: Optional[Union[LstmConfig, LlmConfig]] = None  # 预测配置

class PredictionItem(BaseModel):
    """预测项目模型"""
    date: str  # 预测日期，格式：YYYY-MM-DD
    price: float  # 预测价格
    confidence: float  # 置信度 (0-1)

class AnalysisContentModel(BaseModel):
    """LLM分析内容模型"""
    summary: str  # 分析摘要
    recommendation: str  # 投资建议
    factors: List[str]  # 影响因素
    trend: str  # 趋势 (bullish, bearish, neutral)

class PredictionResult(BaseModel):
    """预测结果模型"""
    code: str  # 股票代码
    name: str  # 股票名称
    date: str  # 预测生成日期，ISO格式
    type: str  # 预测类型，lstm 或 llm
    predictions: List[PredictionItem]  # 预测项目列表
    metrics: Dict[str, float]  # 评估指标
    analysis: Optional[AnalysisContentModel] = None  # LLM分析内容，仅对LLM预测有效

class PredictionTask(BaseModel):
    """预测任务模型"""
    task_id: str  # 任务ID
    code: str  # 股票代码
    start_time: datetime  # 开始时间
    type: str  # 预测类型，lstm 或 llm
    status: str  # 状态, pending, running, completed, error
    progress: float  # 进度 (0-1)
    message: Optional[str] = None  # 任务状态消息

# 系统相关模型

class SystemInfoModel(BaseModel):
    """系统信息模型"""
    version: str
    apiVersion: str
    serverTime: str
    dataLastUpdate: Optional[str] = None
    stockCount: int
    userCount: int

class SystemStatModel(BaseModel):
    """系统统计模型"""
    stockCount: int
    analysisCount: int
    watchlistCount: int
    predictionCount: int

class ErrorModel(BaseModel):
    """错误响应模型"""
    code: int = Field(default=500, description="错误代码")
    message: str = Field(description="错误消息")
    details: Optional[Any] = Field(default=None, description="错误详情")

# 基础响应模型
class ResponseModel(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: str = ""

# 错误响应模型
class ErrorModel(BaseModel):
    success: bool = False
    error: str
    message: str = "操作失败"

# 股票搜索结果项
class StockSearchItem(BaseModel):
    code: str
    name: str
    market: Optional[str] = ""
    industry: Optional[str] = ""

# 股票基本信息
class StockInfo(BaseModel):
    code: str
    name: str
    market: Optional[str] = ""
    price: float = 0
    change: float = 0
    change_percent: float = 0
    volume: int = 0
    amount: float = 0
    industry: Optional[str] = ""
    update_time: str = ""

# K线数据
class StockKline(BaseModel):
    time: str
    open: float
    close: float
    high: float
    low: float
    volume: int
    amount: Optional[float] = 0

# 股票实时价格
class StockPrice(BaseModel):
    code: str
    name: str
    price: float
    change: float
    change_percent: float
    open: float
    close: float
    high: float
    low: float
    volume: int
    amount: float
    time: str

# 公司基本信息
class CompanyInfo(BaseModel):
    code: str
    name: str
    industry: str
    main_business: str
    company_profile: str
    establish_date: str
    listing_date: str
    chairman: str
    general_manager: str
    secretary: str
    registered_capital: str
    employees_count: int
    website: str
    email: str
    office_address: str

# 股票财务信息
class StockFinancials(BaseModel):
    code: str
    name: str
    eps: float
    eps_yoy: float
    bvps: float
    roe: float
    pb: float
    pe: float
    total_mv: float
    circulating_mv: float
    total_revenue: float
    total_revenue_yoy: float
    net_profit: float
    net_profit_yoy: float
    report_date: str 