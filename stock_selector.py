from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QMessageBox, QListWidget,
                               QListWidgetItem, QLabel, QFileDialog)
from PySide6.QtCore import Qt
import json
import os
from stock_search import StockSearchWidget
from stock_chart import show_stock_chart
from work_flow import WorkFlow
from logger_manager import LoggerManager
from analysis_dialog import show_analysis_dialog, export_analysis_results
from strategy_selector import show_strategy_selector

class StockSelector(QMainWindow):
    """股票选择器主窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化日志管理器
        self.logger_manager = LoggerManager()
        self.logger = self.logger_manager.get_logger("stock_selector")
        
        # 选择策略
        self.strategies = show_strategy_selector(self, self.logger_manager)
        if not self.strategies:
            self.logger.warning("未选择任何策略，将使用默认策略")
        
        # 初始化工作流
        self.work_flow = WorkFlow(self.strategies, self.logger_manager)
        
        # 初始化自选股列表
        self.watchlist = []
        
        self.init_ui()
        self.load_watchlist()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("股票选择器")
        self.resize(800, 600)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建工具栏
        toolbar_layout = QHBoxLayout()
        
        # 选择策略按钮
        strategy_btn = QPushButton("选择策略")
        strategy_btn.clicked.connect(self.select_strategies)
        toolbar_layout.addWidget(strategy_btn)
        
        # 批量分析按钮
        batch_analyze_btn = QPushButton("批量分析")
        batch_analyze_btn.clicked.connect(self.batch_analyze_stocks)
        toolbar_layout.addWidget(batch_analyze_btn)
        
        # 导出结果按钮
        export_btn = QPushButton("导出结果")
        export_btn.clicked.connect(self.export_results)
        toolbar_layout.addWidget(export_btn)
        
        # 关于按钮
        about_btn = QPushButton("关于")
        about_btn.clicked.connect(self.show_about_dialog)
        toolbar_layout.addWidget(about_btn)
        
        # 添加弹性空间
        toolbar_layout.addStretch()
        
        main_layout.addLayout(toolbar_layout)
        
        # 创建左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 搜索组件
        self.search_widget = StockSearchWidget(logger_manager=self.logger_manager)
        self.search_widget.stock_selected.connect(self.add_to_watchlist)
        left_layout.addWidget(self.search_widget)
        
        # 自选股列表标签
        watchlist_label = QLabel("自选股列表")
        watchlist_label.setStyleSheet("font-weight: bold; margin: 10px 0;")
        left_layout.addWidget(watchlist_label)
        
        # 自选股列表
        self.watchlist_widget = QListWidget()
        self.watchlist_widget.itemDoubleClicked.connect(self.show_stock_chart)
        left_layout.addWidget(self.watchlist_widget)
        
        main_layout.addWidget(left_panel)
        
    def select_strategies(self):
        """选择策略"""
        strategies = show_strategy_selector(self, self.logger_manager)
        if strategies:
            self.strategies = strategies
            self.work_flow = WorkFlow(self.strategies, self.logger_manager)
            self.logger.info(f"已选择 {len(strategies)} 个策略")
        
    def add_to_watchlist(self, code, name):
        """添加股票到自选股列表"""
        try:
            # 检查是否已存在
            for stock in self.watchlist:
                if stock['code'] == code:
                    self.logger.info(f"股票 {code} 已在自选股列表中")
                    return
            
            # 添加到列表
            stock_info = {'code': code, 'name': name}
            self.watchlist.append(stock_info)
            
            # 添加到界面
            item = QListWidgetItem(f"{code} - {name}")
            item.setData(Qt.UserRole, stock_info)
            self.watchlist_widget.addItem(item)
            
            # 保存到文件
            self.save_watchlist()
            
            self.logger.info(f"添加股票到自选股列表: {code} - {name}")
            
        except Exception as e:
            self.logger.error(f"添加股票失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"添加股票失败: {str(e)}")
            
    def show_stock_chart(self, item):
        """显示股票图表"""
        try:
            stock_info = item.data(Qt.UserRole)
            code = stock_info['code']
            name = stock_info['name']
            
            # 获取股票数据和信号
            data = self.work_flow.get_stock_data(code)
            signals = self.work_flow.get_stock_signals(code)
            
            # 显示图表对话框
            show_stock_chart(code, name, data, signals, self, self.logger_manager)
            
        except Exception as e:
            self.logger.error(f"显示图表失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"显示图表失败: {str(e)}")
            
    def batch_analyze_stocks(self):
        """批量分析自选股"""
        try:
            if not self.watchlist:
                QMessageBox.warning(self, "提示", "自选股列表为空")
                return
                
            results = {}
            for stock in self.watchlist:
                try:
                    result = self.work_flow.analyze_stock(stock['code'])
                    if result:
                        results[f"{stock['code']} - {stock['name']}"] = result
                except Exception as e:
                    self.logger.error(f"分析股票 {stock['code']} 失败: {str(e)}")
                    continue
            
            if results:
                # 显示分析结果
                show_analysis_dialog(
                    "批量分析结果",
                    "自选股分析",
                    results,
                    self,
                    self.logger_manager
                )
            else:
                QMessageBox.warning(self, "提示", "没有可用的分析结果")
                
        except Exception as e:
            self.logger.error(f"批量分析失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"批量分析失败: {str(e)}")
            
    def export_results(self):
        """导出分析结果"""
        try:
            if not self.watchlist:
                QMessageBox.warning(self, "提示", "自选股列表为空")
                return
                
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "导出分析结果",
                "",
                "CSV Files (*.csv)"
            )
            
            if file_name:
                results = {}
                for stock in self.watchlist:
                    try:
                        result = self.work_flow.analyze_stock(stock['code'])
                        if result:
                            results[f"{stock['code']} - {stock['name']}"] = result
                    except Exception as e:
                        self.logger.error(f"分析股票 {stock['code']} 失败: {str(e)}")
                        continue
                
                if results:
                    export_analysis_results(results, file_name)
                    QMessageBox.information(self, "成功", "分析结果已导出")
                else:
                    QMessageBox.warning(self, "提示", "没有可用的分析结果")
                    
        except Exception as e:
            self.logger.error(f"导出结果失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"导出结果失败: {str(e)}")
            
    def save_watchlist(self):
        """保存自选股列表"""
        try:
            watchlist_file = os.path.join("data", "watchlist.json")
            os.makedirs("data", exist_ok=True)
            
            with open(watchlist_file, 'w', encoding='utf-8') as f:
                json.dump(self.watchlist, f, ensure_ascii=False, indent=2)
                
            self.logger.info("保存自选股列表成功")
            
        except Exception as e:
            self.logger.error(f"保存自选股列表失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"保存自选股列表失败: {str(e)}")
            
    def load_watchlist(self):
        """加载自选股列表"""
        try:
            watchlist_file = os.path.join("data", "watchlist.json")
            if os.path.exists(watchlist_file):
                with open(watchlist_file, 'r', encoding='utf-8') as f:
                    self.watchlist = json.load(f)
                    
                # 添加到界面
                for stock in self.watchlist:
                    item = QListWidgetItem(f"{stock['code']} - {stock['name']}")
                    item.setData(Qt.UserRole, stock)
                    self.watchlist_widget.addItem(item)
                    
                self.logger.info(f"加载自选股列表成功: {len(self.watchlist)}只股票")
                
        except Exception as e:
            self.logger.error(f"加载自选股列表失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"加载自选股列表失败: {str(e)}")
            
    def show_about_dialog(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于",
            "股票选择器 v1.0\n\n"
            "基于PySide6的股票分析工具\n"
            "支持股票搜索、自选股管理、K线图显示、技术分析等功能\n\n"
            "作者: Spike\n"
            "版权所有 © 2024"
        )