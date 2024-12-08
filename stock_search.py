from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
from PySide6.QtCore import Signal, Qt
import akshare as ak
import pandas as pd
from pypinyin import lazy_pinyin
from logger_manager import LoggerManager

class StockSearchWidget(QWidget):
    """股票搜索组件"""
    stock_selected = Signal(str, str)  # 股票代码, 股票名称

    def __init__(self, parent=None, logger_manager=None):
        super().__init__(parent)
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("stock_search")
        
        self.init_ui()
        self.load_stock_list()

    def load_stock_list(self):
        """加载股票列表"""
        try:
            # 获取A股列表
            self.stock_df = ak.stock_info_a_code_name()
            self.stock_df['pinyin'] = self.stock_df['name'].apply(lambda x: ''.join(lazy_pinyin(x)))
            self.logger.info(f"成功加载{len(self.stock_df)}只股票信息")
        except Exception as e:
            self.logger.error(f"加载股票列表失败: {str(e)}")
            self.stock_df = pd.DataFrame(columns=['code', 'name', 'pinyin'])

    def filter_stocks(self, text):
        """根据输入过滤股票"""
        try:
            if not text:
                self.list_widget.clear()
                return

            # 转换为小写进行不区分大小写的搜索
            text = text.lower()
            
            # 根据拼音、代码或名称进行过滤
            mask = (
                self.stock_df['pinyin'].str.contains(text, case=False) |
                self.stock_df['code'].str.contains(text, case=False) |
                self.stock_df['name'].str.contains(text, case=False)
            )
            filtered_stocks = self.stock_df[mask]

            # 更新列表
            self.list_widget.clear()
            for _, row in filtered_stocks.iterrows():
                item = QListWidgetItem(f"{row['code']} - {row['name']}")
                item.setData(Qt.UserRole, (row['code'], row['name']))
                self.list_widget.addItem(item)

        except Exception as e:
            self.logger.error(f"过滤股票失败: {str(e)}")

    def on_item_clicked(self, item):
        """处理股票选择"""
        try:
            code, name = item.data(Qt.UserRole)
            self.stock_selected.emit(code, name)
            self.logger.info(f"选择股票: {code} - {name}")
        except Exception as e:
            self.logger.error(f"处理股票选择失败: {str(e)}")

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入股票代码、名称或拼音搜索...")
        self.search_input.textChanged.connect(self.filter_stocks)
        layout.addWidget(self.search_input)
        
        # 股票列表
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)
        
        self.setLayout(layout) 