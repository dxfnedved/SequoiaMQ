# -*- encoding: UTF-8 -*-

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                             QHeaderView, QProgressBar, QMessageBox, QTabWidget)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont
from stock_search import StockSearchWidget
from stock_chart import show_stock_chart
from data_fetcher import DataFetcher
from strategy.alpha_factors101 import Alpha101Strategy
from strategy.RSRS import RSRS_Strategy
from logger_manager import LoggerManager
import pandas as pd
import traceback

class AnalysisThread(QThread):
    """分析线程"""
    progress = Signal(int)  # 进度信号
    result = Signal(tuple)  # 结果信号：(股票代码, 股票名称, 分析结果)
    error = Signal(str)  # 错误信号
    
    def __init__(self, code, name, data_fetcher, strategies):
        super().__init__()
        self.code = code
        self.name = name
        self.data_fetcher = data_fetcher
        self.strategies = strategies
        
    def run(self):
        try:
            # 获取数据
            code = self.code[0] if isinstance(self.code, tuple) else self.code
            data = self.data_fetcher.fetch_stock_data((code, self.name))
            if data is None:
                self.error.emit(f"获取{self.code} {self.name}数据失败")
                return
                
            # 分析数据
            results = {}
            for strategy in self.strategies:
                strategy_result = strategy.analyze(data)
                if strategy_result:
                    results[strategy.name] = strategy_result
                    
            self.result.emit((self.code, self.name, results))
            
        except Exception as e:
            self.error.emit(f"分析{self.code} {self.name}失败: {str(e)}")

class StockSelector(QMainWindow):
    """股票选择器主窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化日志管理器
        self.logger_manager = LoggerManager()
        self.logger = self.logger_manager.get_logger("stock_selector")
        
        self.init_ui()
        self.init_data()
        
    def init_data(self):
        """初始化数据和策略"""
        self.data_fetcher = DataFetcher(self.logger_manager)
        self.strategies = [
            Alpha101Strategy(),
            RSRS_Strategy()
        ]
        self.analysis_threads = []
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('股票分���器')
        self.setMinimumSize(1200, 800)
        
        # 创建中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 搜索组件
        self.search_widget = StockSearchWidget(logger_manager=self.logger_manager)
        self.search_widget.stock_selected.connect(self.on_stock_selected)
        left_layout.addWidget(self.search_widget)
        
        # 按钮组
        button_layout = QHBoxLayout()
        self.analyze_btn = QPushButton('分析选中股票')
        self.analyze_btn.clicked.connect(self.analyze_selected_stock)
        self.batch_analyze_btn = QPushButton('批量分析')
        self.batch_analyze_btn.clicked.connect(self.batch_analyze)
        button_layout.addWidget(self.analyze_btn)
        button_layout.addWidget(self.batch_analyze_btn)
        left_layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(left_panel, 1)
        
        # 右侧面板（使用选项���）
        self.tab_widget = QTabWidget()
        
        # 分析结果表格选项卡
        self.result_table = QTableWidget()
        self.setup_result_table()
        self.tab_widget.addTab(self.result_table, "分析结果")
        
        # 信号列表选项卡
        self.signal_table = QTableWidget()
        self.setup_signal_table()
        self.tab_widget.addTab(self.signal_table, "交易信号")
        
        main_layout.addWidget(self.tab_widget, 2)
        
    def setup_result_table(self):
        """设置分析结果表格"""
        self.result_table.setColumnCount(7)
        self.result_table.setHorizontalHeaderLabels([
            '股票代码', '股票名称', 'Alpha101_Alpha1', 'Alpha101_Alpha2',
            'Alpha101_Alpha3', 'Alpha101_Alpha4', 'RARA策略'
        ])
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
    def setup_signal_table(self):
        """设置信号表格"""
        self.signal_table.setColumnCount(5)
        self.signal_table.setHorizontalHeaderLabels([
            '股票代码', '股票名称', '策略', '信号类型', '信号强度'
        ])
        header = self.signal_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
    def on_stock_selected(self, code, name):
        """处理股票选择"""
        self.current_code = code
        self.current_name = name
        self.analyze_btn.setEnabled(True)
        
    def analyze_selected_stock(self):
        """分析选中的股票"""
        if hasattr(self, 'current_code'):
            self.start_analysis([self.current_code], [self.current_name])
            
    def batch_analyze(self):
        """批量分析自选股"""
        try:
            # 从自选股列表获取股票
            stocks = self.search_widget.stock_df
            if stocks is None or stocks.empty:
                QMessageBox.warning(self, "警告", "没有可分析的股票")
                return
                
            codes = stocks['code'].tolist()
            names = stocks['name'].tolist()
            
            # 开始分析
            self.start_analysis(codes, names)
            
        except Exception as e:
            self.logger.error(f"批量分析失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            QMessageBox.critical(self, "错误", f"批量分析失败: {str(e)}")
            
    def start_analysis(self, codes, names):
        """开始分析流程"""
        # 清空表格
        self.result_table.setRowCount(0)
        self.signal_table.setRowCount(0)
        
        # 设置进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(codes))
        self.progress_bar.setValue(0)
        
        # 创建并启动分析线程
        self.analysis_threads.clear()
        for code, name in zip(codes, names):
            thread = AnalysisThread(code, name, self.data_fetcher, self.strategies)
            thread.result.connect(self.handle_analysis_result)
            thread.error.connect(self.handle_analysis_error)
            thread.finished.connect(lambda: self.progress_bar.setValue(self.progress_bar.value() + 1))
            self.analysis_threads.append(thread)
            thread.start()
            
    def handle_analysis_result(self, result):
        """处理分析结果"""
        code, name, strategy_results = result
        
        # 添加到结果表格
        row = self.result_table.rowCount()
        self.result_table.insertRow(row)
        
        # 设置股票信息
        self.result_table.setItem(row, 0, QTableWidgetItem(code))
        self.result_table.setItem(row, 1, QTableWidgetItem(name))
        
        # 设置策略结果
        if 'Alpha101Strategy' in strategy_results:
            alpha_results = strategy_results['Alpha101Strategy']
            for i, key in enumerate(['Alpha101Strategy_Alpha1', 'Alpha101Strategy_Alpha2', 
                                   'Alpha101Strategy_Alpha3', 'Alpha101Strategy_Alpha4']):
                value = alpha_results.get(key, 'N/A')
                item = QTableWidgetItem(str(value))
                self.result_table.setItem(row, i + 2, item)
                
        if 'RARA' in strategy_results:
            rara_result = strategy_results['RARA']
            item = QTableWidgetItem(str(rara_result.get('signal', 'N/A')))
            self.result_table.setItem(row, 6, item)
            
        # 添加到信号表格
        self.add_signals_to_table(code, name, strategy_results)
        
    def add_signals_to_table(self, code, name, strategy_results):
        """添加信号到信号表格"""
        for strategy_name, results in strategy_results.items():
            signals = []
            if strategy_name == 'Alpha101Strategy':
                signal = results.get('Alpha101Strategy_Alpha101_信号', '')
                if signal and signal != '无':
                    signals.append(('Alpha101策略', signal, len(signal.split(';'))))
            elif strategy_name == 'RARA':
                signal = results.get('signal', '')
                if signal and signal != '无':
                    signals.append(('RARA策略', signal, 1))
                    
            for strategy, signal, strength in signals:
                row = self.signal_table.rowCount()
                self.signal_table.insertRow(row)
                
                self.signal_table.setItem(row, 0, QTableWidgetItem(code))
                self.signal_table.setItem(row, 1, QTableWidgetItem(name))
                self.signal_table.setItem(row, 2, QTableWidgetItem(strategy))
                self.signal_table.setItem(row, 3, QTableWidgetItem(signal))
                self.signal_table.setItem(row, 4, QTableWidgetItem(str(strength)))
                
                # 设置颜色
                if '买入' in signal or '看多' in signal:
                    color = QColor(255, 240, 240)  # 浅红色
                elif '卖出' in signal or '看空' in signal:
                    color = QColor(240, 255, 240)  # 浅绿色
                else:
                    color = QColor(255, 255, 255)  # 白色
                    
                for col in range(5):
                    self.signal_table.item(row, col).setBackground(color)
                    
    def handle_analysis_error(self, error_msg):
        """处理分析错误"""
        self.logger.error(error_msg)
        
    def closeEvent(self, event):
        """关闭窗口时清理资源"""
        for thread in self.analysis_threads:
            thread.quit()
            thread.wait()
        event.accept() 