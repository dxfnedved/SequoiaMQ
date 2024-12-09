class BaseStrategy:
    """策略基类"""
    def __init__(self):
        self.name = "BaseStrategy"
        
    def analyze(self, data):
        """
        分析数据
        Args:
            data: DataFrame, 包含OHLCV数据
        Returns:
            dict: 分析结果
        """
        raise NotImplementedError("策略必须实现analyze方法")
        
    def get_signals(self, data):
        """
        获取买卖信号
        Args:
            data: DataFrame, 包含OHLCV数据
        Returns:
            list: 信号列表，每个信号是一个字典，包含：
                - date: 信号日期
                - type: 信号类型（买入/卖出）
                - strategy: 策略名称
                - price: 信号价格
                - 其他策略特定信息
        """
        raise NotImplementedError("策略必须实现get_signals方法") 