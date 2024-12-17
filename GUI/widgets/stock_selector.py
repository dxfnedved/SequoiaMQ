"""Stock selector widget implementation."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from data_fetcher import DataFetcher
from logger_manager import LoggerManager
from .strategy_analyzer import StrategyAnalyzer

class AnalysisThread(QThread):
    """分析线程"""
    progress = Signal(int)  # 进度信号
    result = Signal(tuple)  # 结果信号：(股票代码, 股票名称, 分析结果)
    error = Signal(str)  # 错误信号
    
    def __init__(self, code, name, data_fetcher, strategy_analyzer):
        super().__init__()
        self.code = code
        self.name = name
        self.data_fetcher = data_fetcher
        self.strategy_analyzer = strategy_analyzer
        
    def run(self):
        try:
            # 获取数据
            data = self.data_fetcher.fetch_stock_data(self.code)
            if data is None:
                self.error.emit(f"获取{self.code} {self.name}数据失败")
                return
                
            # 分析数据
            results = self.strategy_analyzer.analyze_stock(self.code)
            if results:
                self.result.emit((self.code, self.name, results))
            else:
                self.error.emit(f"分析{self.code} {self.name}失败")
                
        except Exception as e:
            self.error.emit(f"分析{self.code} {self.name}失败: {str(e)}")

class StockSelector(QWidget):
    """股票选择器组件"""
    def __init__(self, logger_manager=None, parent=None):
        super().__init__(parent)
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("stock_selector")
        
        self.data_fetcher = DataFetcher(logger_manager=self.logger_manager)
        self.strategy_analyzer = StrategyAnalyzer(logger_manager=self.logger_manager)
        
        self.analysis_threads = []
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 结果表格
        self.result_table = QTableWidget()
        self.setup_result_table()
        layout.addWidget(self.result_table)
        
    def setup_result_table(self):
        """设置结果表格"""
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels([
            '股票代码', '股票名称', '策略结果', '信号'
        ])
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
    def analyze_stocks(self, stocks):
        """分析股票列表"""
        try:
            # 清空表格
            self.result_table.setRowCount(0)
            
            # 设置进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(len(stocks))
            self.progress_bar.setValue(0)
            
            # 创建并启动分析线程
            self.analysis_threads.clear()
            for code, name in stocks:
                thread = AnalysisThread(
                    code, name,
                    self.data_fetcher,
                    self.strategy_analyzer
                )
                thread.result.connect(self.handle_analysis_result)
                thread.error.connect(self.handle_analysis_error)
                thread.finished.connect(
                    lambda: self.progress_bar.setValue(
                        self.progress_bar.value() + 1
                    )
                )
                self.analysis_threads.append(thread)
                thread.start()
                
        except Exception as e:
            self.logger.error(f"启动分析失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"启动分析失败: {str(e)}")
            
    def handle_analysis_result(self, result):
        """处理分析结果"""
        try:
            code, name, strategy_results = result
            
            # 添加到结果表格
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            
            # 设置股票信息
            self.result_table.setItem(row, 0, QTableWidgetItem(code))
            self.result_table.setItem(row, 1, QTableWidgetItem(name))
            
            # 设置策略结果
            strategy_text = ""
            signal_text = ""
            for strategy, result in strategy_results.items():
                if strategy != 'timestamp' and strategy != 'code':
                    strategy_text += f"{strategy}:\n"
                    for key, value in result.items():
                        if key == 'signal':
                            signal_text += f"{strategy}: {value}\n"
                        else:
                            strategy_text += f"  {key}: {value}\n"
                            
            self.result_table.setItem(row, 2, QTableWidgetItem(strategy_text))
            self.result_table.setItem(row, 3, QTableWidgetItem(signal_text))
            
        except Exception as e:
            self.logger.error(f"处理分析结果失败: {str(e)}")
            
    def handle_analysis_error(self, error_msg):
        """处理分析错误"""
        self.logger.error(error_msg)
        QMessageBox.warning(self, "警告", error_msg) 