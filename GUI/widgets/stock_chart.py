"""Stock chart widget implementation."""

from PySide6.QtWidgets import QWidget, QVBoxLayout
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import mplfinance as mpf
import pandas as pd
from data_fetcher import DataFetcher
from logger_manager import LoggerManager

class StockChartWidget(QWidget):
    """股票K线图组件"""
    def __init__(self, logger_manager=None, parent=None):
        super().__init__(parent)
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("stock_chart")
        self.data_fetcher = DataFetcher(logger_manager=self.logger_manager)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建图表
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
    def update_chart(self, code, name):
        """更新图表"""
        try:
            # 获取数据
            data = self.data_fetcher.fetch_stock_data((code, name))
            if data is None:
                self.logger.error(f"获取股票 {code} 数据失败")
                return
                
            # 清除旧图表
            self.figure.clear()
            
            # 创建K线图
            ax = self.figure.add_subplot(111)
            mpf.plot(data, type='candle', style='charles',
                    title=f'{name} ({code})',
                    ylabel='价格',
                    volume=True,
                    ax=ax,
                    volume_panel=2,
                    show_nontrading=False)
            
            # 刷新画布
            self.canvas.draw()
            
        except Exception as e:
            self.logger.error(f"更新图表失败: {str(e)}")
            
    def clear_chart(self):
        """清除图表"""
        self.figure.clear()
        self.canvas.draw() 