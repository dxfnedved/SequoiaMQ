"""Stock search widget implementation."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide6.QtCore import Signal, Qt
from pypinyin import lazy_pinyin, Style
import pandas as pd
from data_fetcher import DataFetcher
from logger_manager import LoggerManager

class StockSearchWidget(QWidget):
    """股票搜索组件"""
    stock_selected = Signal(str, str)  # 股票代码, 股票名称
    
    def __init__(self, logger_manager=None, parent=None):
        super().__init__(parent)
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("stock_search")
        self.data_fetcher = DataFetcher(logger_manager=self.logger_manager)
        
        self.init_ui()
        self.load_stock_list()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入股票代码、名称或拼音搜索...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        layout.addWidget(self.search_input)
        
        # 搜索结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(['代码', '名称'])
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.result_table.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.result_table)
        
    def load_stock_list(self):
        """加载股票列表"""
        try:
            stock_list = self.data_fetcher.get_stock_list()
            if not stock_list:
                self.logger.error("获取股票列表失败")
                return
                
            # 转换为DataFrame并添加拼音列
            self.stock_df = pd.DataFrame(stock_list)
            self.stock_df['pinyin'] = self.stock_df['name'].apply(
                lambda x: ''.join(lazy_pinyin(x, style=Style.FIRST_LETTER))
            )
            self.stock_df['pinyin_full'] = self.stock_df['name'].apply(
                lambda x: ''.join(lazy_pinyin(x))
            )
            
            self.logger.info(f"加载了 {len(stock_list)} 只股票")
            
        except Exception as e:
            self.logger.error(f"加载股票列表失败: {str(e)}")
            
    def on_search_text_changed(self, text):
        """处理搜索文本变化"""
        try:
            if not text:
                self.result_table.setRowCount(0)
                return
                
            # 搜索匹配
            text = text.lower()
            mask = (
                self.stock_df['code'].str.contains(text) |
                self.stock_df['name'].str.contains(text) |
                self.stock_df['pinyin'].str.contains(text) |
                self.stock_df['pinyin_full'].str.contains(text)
            )
            matched = self.stock_df[mask]
            
            # 更新表格
            self.result_table.setRowCount(len(matched))
            for i, (_, stock) in enumerate(matched.iterrows()):
                self.result_table.setItem(i, 0, QTableWidgetItem(stock['code']))
                self.result_table.setItem(i, 1, QTableWidgetItem(stock['name']))
                
        except Exception as e:
            self.logger.error(f"搜索失败: {str(e)}")
            
    def on_item_double_clicked(self, item):
        """处理股票选择"""
        try:
            row = item.row()
            code = self.result_table.item(row, 0).text()
            name = self.result_table.item(row, 1).text()
            self.stock_selected.emit(code, name)
            
        except Exception as e:
            self.logger.error(f"处理股票选择失败: {str(e)}") 