# -*- encoding: UTF-8 -*-

from logger_manager import LoggerManager

class BaseStrategy:
    """策略基类"""
    def __init__(self, logger_manager=None):
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger(self.__class__.__name__)
        
    def analyze(self, data):
        """
        分析数据
        :param data: DataFrame 股票数据
        :return: dict 分析结果
        """
        raise NotImplementedError("子类必须实现analyze方法")
        
    def get_signals(self, data):
        """
        获取买卖信号
        :param data: DataFrame 股票数据
        :return: list 信号列表
        """
        raise NotImplementedError("子类必须实现get_signals方法")
        
    def _validate_data(self, data):
        """
        验证数据有效性
        :param data: DataFrame 股票数据
        :return: bool 数据是否有效
        """
        try:
            if data is None or data.empty:
                self.logger.warning("数据为空")
                return False
                
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                self.logger.warning(f"数据缺少必要列: {missing_columns}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"数据验证失败: {str(e)}")
            return False 