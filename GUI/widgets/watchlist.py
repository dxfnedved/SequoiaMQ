"""Watchlist widget implementation."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal
import pandas as pd
import json
import os
from data_fetcher import DataFetcher
from logger_manager import LoggerManager

class WatchlistWidget(QWidget):
    """自选股列表组件"""
    stock_double_clicked = Signal(str, str)  # 股票代码, 股票名称
    analyze_stocks = Signal(list)  # [(code, name), ...]
    
    def __init__(self, logger_manager=None, parent=None):
        super().__init__(parent)
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("watchlist")
        self.data_fetcher = DataFetcher(logger_manager=self.logger_manager)
        
        self.watchlist_file = 'data/watchlist.json'
        os.makedirs('data', exist_ok=True)
        
        self.init_ui()
        self.load_watchlist()
        
        # 定时更新
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_prices)
        self.update_timer.start(60000)  # 每分钟更新一次
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.select_all_cb = QCheckBox("全选")
        self.select_all_cb.stateChanged.connect(self.on_select_all_changed)
        toolbar.addWidget(self.select_all_cb)
        
        self.analyze_btn = QPushButton("分析选中")
        self.analyze_btn.clicked.connect(self.on_analyze_clicked)
        toolbar.addWidget(self.analyze_btn)
        
        self.remove_btn = QPushButton("删除选中")
        self.remove_btn.clicked.connect(self.remove_selected)
        toolbar.addWidget(self.remove_btn)
        
        layout.addLayout(toolbar)
        
        # 自选股表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['', '代码', '名称', '最新价', '涨跌幅'])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.table)
        
    def load_watchlist(self):
        """加载自选股列表"""
        try:
            if os.path.exists(self.watchlist_file):
                with open(self.watchlist_file, 'r', encoding='utf-8') as f:
                    watchlist = json.load(f)
            else:
                watchlist = []
                
            self.update_table(watchlist)
            self.logger.info(f"加载了 {len(watchlist)} 只自选股")
            
        except Exception as e:
            self.logger.error(f"加载自选股列表失败: {str(e)}")
            
    def save_watchlist(self):
        """保存自选股列表"""
        try:
            watchlist = []
            for row in range(self.table.rowCount()):
                code = self.table.item(row, 1).text()
                name = self.table.item(row, 2).text()
                watchlist.append({'code': code, 'name': name})
                
            with open(self.watchlist_file, 'w', encoding='utf-8') as f:
                json.dump(watchlist, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"保存了 {len(watchlist)} 只自选股")
            
        except Exception as e:
            self.logger.error(f"保存自选股列表失败: {str(e)}")
            
    def update_table(self, watchlist):
        """更新表格"""
        self.table.setRowCount(len(watchlist))
        for i, stock in enumerate(watchlist):
            # 复选框
            cb = QCheckBox()
            self.table.setCellWidget(i, 0, cb)
            
            # 股票信息
            self.table.setItem(i, 1, QTableWidgetItem(stock['code']))
            self.table.setItem(i, 2, QTableWidgetItem(stock['name']))
            self.table.setItem(i, 3, QTableWidgetItem('--'))
            self.table.setItem(i, 4, QTableWidgetItem('--'))
            
    def update_prices(self):
        """更新价格"""
        try:
            for row in range(self.table.rowCount()):
                code = self.table.item(row, 1).text()
                name = self.table.item(row, 2).text()
                
                # 获取最新价格
                price_data = self.data_fetcher.fetch_realtime_price((code, name))
                if price_data:
                    self.table.setItem(row, 3, QTableWidgetItem(f"{price_data['price']:.2f}"))
                    self.table.setItem(row, 4, QTableWidgetItem(f"{price_data['change']:.2f}%"))
                    
                    # 设置颜色
                    color = Qt.red if price_data['change'] > 0 else Qt.green
                    self.table.item(row, 3).setForeground(color)
                    self.table.item(row, 4).setForeground(color)
                    
        except Exception as e:
            self.logger.error(f"更新价格失败: {str(e)}")
            
    def add_stock(self, code, name):
        """添加股票"""
        try:
            # 检查是否已存在
            for row in range(self.table.rowCount()):
                if self.table.item(row, 1).text() == code:
                    return
                    
            # 添加新行
            row = self.table.rowCount()
            self.table.setRowCount(row + 1)
            
            # 复选框
            cb = QCheckBox()
            self.table.setCellWidget(row, 0, cb)
            
            # 股票信息
            self.table.setItem(row, 1, QTableWidgetItem(code))
            self.table.setItem(row, 2, QTableWidgetItem(name))
            self.table.setItem(row, 3, QTableWidgetItem('--'))
            self.table.setItem(row, 4, QTableWidgetItem('--'))
            
            # 保存
            self.save_watchlist()
            
        except Exception as e:
            self.logger.error(f"添加股票失败: {str(e)}")
            
    def remove_selected(self):
        """删除选中的股票"""
        try:
            rows_to_remove = []
            for row in range(self.table.rowCount()):
                cb = self.table.cellWidget(row, 0)
                if cb and cb.isChecked():
                    rows_to_remove.append(row)
                    
            # 从后往前删除
            for row in reversed(rows_to_remove):
                self.table.removeRow(row)
                
            # 保存
            self.save_watchlist()
            
        except Exception as e:
            self.logger.error(f"删除股票失败: {str(e)}")
            
    def on_select_all_changed(self, state):
        """处理全选状态变化"""
        try:
            for row in range(self.table.rowCount()):
                cb = self.table.cellWidget(row, 0)
                if cb:
                    cb.setChecked(state == Qt.Checked)
                    
        except Exception as e:
            self.logger.error(f"设置全选状态失败: {str(e)}")
            
    def on_analyze_clicked(self):
        """处理分析按钮点击"""
        try:
            selected_stocks = []
            for row in range(self.table.rowCount()):
                cb = self.table.cellWidget(row, 0)
                if cb and cb.isChecked():
                    code = self.table.item(row, 1).text()
                    name = self.table.item(row, 2).text()
                    selected_stocks.append((code, name))
                    
            if selected_stocks:
                self.analyze_stocks.emit(selected_stocks)
            else:
                QMessageBox.warning(self, "警告", "请先选择要分析的股票")
                
        except Exception as e:
            self.logger.error(f"处理分析请求失败: {str(e)}")
            
    def on_item_double_clicked(self, item):
        """处理股票双击"""
        try:
            row = item.row()
            code = self.table.item(row, 1).text()
            name = self.table.item(row, 2).text()
            self.stock_double_clicked.emit(code, name)
            
        except Exception as e:
            self.logger.error(f"处理股票双击失败: {str(e)}") 