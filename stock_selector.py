from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QMessageBox, QMenuBar, QMenu, 
                               QFileDialog, QDialog)
from PySide6.QtCore import Qt
import pandas as pd
import os
import json
from datetime import datetime
from stock_search import StockSearchWidget
from stock_chart import StockChartDialog
from data_fetcher import DataFetcher
from strategy_analyzer import StrategyAnalyzer
from logger_manager import LoggerManager

class StockSelector(QMainWindow):
    """股票选择器主窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化日志管理器
        self.logger_manager = LoggerManager()
        self.logger = self.logger_manager.get_logger("stock_selector")
        
        # 初始化组件
        self.data_fetcher = DataFetcher(logger_manager=self.logger_manager)
        self.strategy_analyzer = StrategyAnalyzer(logger_manager=self.logger_manager)
        
        # 初始化数据
        self.watchlist = []
        self.init_ui()
        self.load_watchlist()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('股票选择器')
        self.setMinimumSize(800, 600)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        
        # 搜索组件
        self.search_widget = StockSearchWidget(logger_manager=self.logger_manager)
        self.search_widget.stock_selected.connect(self.on_stock_selected)
        layout.addWidget(self.search_widget)
        
        # 自选股列表标签
        watchlist_label = QLabel("自选股列表")
        watchlist_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px 0;")
        layout.addWidget(watchlist_label)
        
        # 自选股列表布局
        self.watchlist_layout = QVBoxLayout()
        layout.addLayout(self.watchlist_layout)
        
        # 添加弹性空间
        layout.addStretch()

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        # 导入自选股
        import_action = file_menu.addAction('导入自选股')
        import_action.triggered.connect(self.import_watchlist)
        
        # 导出自选股
        export_action = file_menu.addAction('导出自选股')
        export_action.triggered.connect(self.export_watchlist)
        
        # 导出Excel报告
        export_excel_action = file_menu.addAction('导出Excel报告')
        export_excel_action.triggered.connect(self.export_excel_report)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        about_action = help_menu.addAction('关于')
        about_action.triggered.connect(self.show_about_dialog)

    def on_stock_selected(self, code, name):
        """处理股票选择"""
        try:
            # 检查是否已在自选股列表中
            if any(stock['code'] == code for stock in self.watchlist):
                self.logger.info(f"股票 {code} 已在自选股列表中")
                return
            
            # 添加到自选股列表
            stock_info = {'code': code, 'name': name}
            self.watchlist.append(stock_info)
            self.add_stock_widget(stock_info)
            self.save_watchlist()
            
            self.logger.info(f"添加股票到自选股列表: {code} - {name}")
            
        except Exception as e:
            self.logger.error(f"添加股票失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"添加股票失败: {str(e)}")

    def add_stock_widget(self, stock_info):
        """添加股票组件到界面"""
        try:
            # 创建水平布局
            stock_layout = QHBoxLayout()
            
            # 股票信息标签
            stock_label = QLabel(f"{stock_info['code']} - {stock_info['name']}")
            stock_layout.addWidget(stock_label)
            
            # 查看走势按钮
            chart_btn = QPushButton("查看走势")
            chart_btn.clicked.connect(lambda: self.show_stock_chart(stock_info['code'], stock_info['name']))
            stock_layout.addWidget(chart_btn)
            
            # 分析按钮
            analyze_btn = QPushButton("分析")
            analyze_btn.clicked.connect(lambda: self.analyze_stock(stock_info['code']))
            stock_layout.addWidget(analyze_btn)
            
            # 删除按钮
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda: self.remove_stock(stock_info['code'], stock_layout))
            stock_layout.addWidget(delete_btn)
            
            # 添加到主布局
            self.watchlist_layout.addLayout(stock_layout)
            
        except Exception as e:
            self.logger.error(f"添加股票组件失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"添加股票组件失败: {str(e)}")

    def show_stock_chart(self, code, name):
        """显示股票走势图"""
        try:
            # 获取股票数据
            data = self.data_fetcher.fetch_stock_data(code)
            if data is None or data.empty:
                self.logger.error(f"获取股票 {code} 数据失败")
                QMessageBox.warning(self, "错误", "获取股票数据失败")
                return
            
            # 显示走势图对话框
            dialog = StockChartDialog(code, name, data, logger_manager=self.logger_manager, parent=self)
            dialog.exec_()
            
        except Exception as e:
            self.logger.error(f"显示走势图失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"显示走势图失败: {str(e)}")

    def analyze_stock(self, code):
        """分析股票"""
        try:
            # 获取股票数据
            data = self.data_fetcher.fetch_stock_data(code)
            if data is None or data.empty:
                self.logger.error(f"获取股票 {code} 数据失败")
                QMessageBox.warning(self, "错误", "获取股票数据失败")
                return
            
            # 进行策略分析
            results = self.strategy_analyzer.analyze_stocks([data])
            if not results:
                self.logger.error(f"分析股票 {code} 失败")
                QMessageBox.warning(self, "错误", "分析股票失败")
                return
            
            # 显示分析结果
            result_text = "\n".join([f"{k}: {v}" for k, v in results[0].items()])
            QMessageBox.information(self, "分析结果", result_text)
            
        except Exception as e:
            self.logger.error(f"分析股票失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"分析股票失败: {str(e)}")

    def remove_stock(self, code, layout):
        """从自选股列表中删除股票"""
        try:
            # 从数据中删除
            self.watchlist = [stock for stock in self.watchlist if stock['code'] != code]
            self.save_watchlist()
            
            # 从界面中删除
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.watchlist_layout.removeItem(layout)
            
            self.logger.info(f"删除股票: {code}")
            
        except Exception as e:
            self.logger.error(f"删除股票失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"删除股票失败: {str(e)}")

    def save_watchlist(self):
        """保存自选股列表"""
        try:
            watchlist_file = "watchlist.json"
            with open(watchlist_file, 'w', encoding='utf-8') as f:
                json.dump(self.watchlist, f, ensure_ascii=False, indent=2)
            self.logger.info("保存自选股列表成功")
        except Exception as e:
            self.logger.error(f"保存自选股列表失败: {str(e)}")

    def load_watchlist(self):
        """加载自选股列表"""
        try:
            watchlist_file = "watchlist.json"
            if os.path.exists(watchlist_file):
                with open(watchlist_file, 'r', encoding='utf-8') as f:
                    self.watchlist = json.load(f)
                    
                # 添加到界面
                for stock in self.watchlist:
                    self.add_stock_widget(stock)
                    
                self.logger.info(f"加载自选股列表成功: {len(self.watchlist)}只股票")
        except Exception as e:
            self.logger.error(f"加载自选股列表失败: {str(e)}")

    def import_watchlist(self):
        """导入自选股列表"""
        try:
            file_name, _ = QFileDialog.getOpenFileName(
                self, "选择自选股文件", "", "JSON Files (*.json);;All Files (*)"
            )
            
            if file_name:
                with open(file_name, 'r', encoding='utf-8') as f:
                    imported_list = json.load(f)
                
                # 清除现有列表
                self.watchlist.clear()
                while self.watchlist_layout.count():
                    item = self.watchlist_layout.takeAt(0)
                    if item.layout():
                        while item.layout().count():
                            sub_item = item.layout().takeAt(0)
                            if sub_item.widget():
                                sub_item.widget().deleteLater()
                
                # 添加导入的股票
                for stock in imported_list:
                    self.watchlist.append(stock)
                    self.add_stock_widget(stock)
                
                self.save_watchlist()
                self.logger.info(f"导入自选股列表成功: {len(imported_list)}只股票")
                QMessageBox.information(self, "成功", "导入自选股列表成功")
                
        except Exception as e:
            self.logger.error(f"导入自选股列表失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"导入自选股列表失败: {str(e)}")

    def export_watchlist(self):
        """导出自选股列表"""
        try:
            file_name, _ = QFileDialog.getSaveFileName(
                self, "保存自选股文件", "", "JSON Files (*.json);;All Files (*)"
            )
            
            if file_name:
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(self.watchlist, f, ensure_ascii=False, indent=2)
                self.logger.info("导出自选股列表成功")
                QMessageBox.information(self, "成功", "导出自选股列表成功")
                
        except Exception as e:
            self.logger.error(f"导出自选股列表失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"导出自选股列表失败: {str(e)}")

    def export_excel_report(self):
        """导出Excel分析报告"""
        try:
            if not self.watchlist:
                QMessageBox.warning(self, "警告", "自选股列表为空")
                return
            
            file_name, _ = QFileDialog.getSaveFileName(
                self, "保存Excel报告", "", "Excel Files (*.xlsx);;All Files (*)"
            )
            
            if file_name:
                # 获取所有股票数据
                all_data = []
                for stock in self.watchlist:
                    data = self.data_fetcher.fetch_stock_data(stock['code'])
                    if data is not None and not data.empty:
                        all_data.append(data)
                
                # 分析所有股票
                results = self.strategy_analyzer.analyze_stocks(all_data)
                
                # 创建DataFrame
                report_data = []
                for stock, result in zip(self.watchlist, results):
                    row = {
                        '股票代码': stock['code'],
                        '股票名称': stock['name'],
                        '分析时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        **result
                    }
                    report_data.append(row)
                
                df = pd.DataFrame(report_data)
                df.to_excel(file_name, index=False)
                
                self.logger.info("导出Excel报告成功")
                QMessageBox.information(self, "成功", "导出Excel报告成功")
                
        except Exception as e:
            self.logger.error(f"导出Excel报告失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"导出Excel报告失败: {str(e)}")

    def show_about_dialog(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于",
            "股票选择器 v1.0\n\n"
            "基于PySide6的股票分析工具\n"
            "支持股票搜索、K线图显示、技术分析等功能\n\n"
            "作者: Your Name\n"
            "版权所有 © 2024"
        )