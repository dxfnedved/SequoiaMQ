"""Main window implementation for SequoiaMQ GUI."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt

from .widgets.stock_search import StockSearchWidget
from .widgets.stock_chart import StockChartWidget
from .widgets.watchlist import WatchlistWidget
from .widgets.strategy_selector import StrategySelector
from .widgets.strategy_analyzer import StrategyAnalyzer
from .dialogs.analysis_dialog import show_analysis_dialog
from work_flow import WorkFlow
from logger_manager import LoggerManager

class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化日志管理器
        self.logger_manager = LoggerManager()
        self.logger = self.logger_manager.get_logger("main_window")
        
        # 初始化工作流
        self.work_flow = WorkFlow(logger_manager=self.logger_manager)
        self.strategy_analyzer = StrategyAnalyzer(logger_manager=self.logger_manager)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('SequoiaMQ 量化交易系统')
        self.setMinimumSize(1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QHBoxLayout(central_widget)
        
        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 股票搜索组件
        self.stock_search = StockSearchWidget(logger_manager=self.logger_manager)
        self.stock_search.stock_selected.connect(self.on_stock_selected)
        left_layout.addWidget(self.stock_search)
        
        # 自选股列表
        self.watchlist = WatchlistWidget(logger_manager=self.logger_manager)
        self.watchlist.stock_double_clicked.connect(self.on_stock_selected)
        self.watchlist.analyze_stocks.connect(self.analyze_stocks)
        left_layout.addWidget(self.watchlist)
        
        layout.addWidget(left_panel, stretch=1)
        
        # 右侧标签页
        tab_widget = QTabWidget()
        
        # K线图标签页
        self.stock_chart = StockChartWidget(logger_manager=self.logger_manager)
        tab_widget.addTab(self.stock_chart, "K线图")
        
        # 策略选择标签页
        self.strategy_selector = StrategySelector(logger_manager=self.logger_manager)
        self.strategy_selector.strategies_changed.connect(self.on_strategies_changed)
        tab_widget.addTab(self.strategy_selector, "策略选择")
        
        layout.addWidget(tab_widget, stretch=2)
        
    def on_stock_selected(self, code, name):
        """处理股票选择"""
        try:
            self.current_code = code
            self.current_name = name
            self.logger.info(f"选择股票: {code} - {name}")
            
            # 更新图表
            self.stock_chart.update_chart(code, name)
            
            # 添加到自选股
            self.watchlist.add_stock(code, name)
            
        except Exception as e:
            self.logger.error(f"处理股票选择失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"处理股票选择失败: {str(e)}")
            
    def on_strategies_changed(self, strategies):
        """处理策略选择变化"""
        try:
            self.work_flow.set_strategies(strategies)
            self.logger.info(f"更新策略: {strategies}")
        except Exception as e:
            self.logger.error(f"更新策略失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"更新策略失败: {str(e)}")
            
    def analyze_stocks(self, stocks):
        """分析股票"""
        try:
            for code, name in stocks:
                # 获取分析结果
                results = self.strategy_analyzer.analyze_stock(code)
                
                # 显示分析结果对话框
                show_analysis_dialog(
                    code,
                    name,
                    results,
                    self,
                    self.logger_manager
                )
                
        except Exception as e:
            self.logger.error(f"分析股票失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"分析股票失败: {str(e)}") 