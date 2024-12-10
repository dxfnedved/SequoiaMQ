from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QCompleter, QComboBox
)
from PySide6.QtCore import Signal, Qt
from stock_cache import stock_cache
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
            # 使用缓存管理器加载股票列表
            self.stock_df = stock_cache.load_stock_list()
            self.logger.info(f"成功加载{len(self.stock_df)}只股票信息")
            
            # 创建搜索用的字符串列表
            self.search_items = []
            for _, row in self.stock_df.iterrows():
                # 创建显示文本
                display_text = f"{row['code']} - {row['name']} ({row['pinyin_initials']})"
                self.search_items.append(display_text)
                
            # 更新自动完成器
            self.completer.setModel(self.search_items)
            
        except Exception as e:
            self.logger.error(f"加载股票列表失败: {str(e)}")

    def on_text_changed(self, text):
        """处理输入文本变化"""
        try:
            if not text:
                return

            # 转换为小写进行不区分大小写的搜索
            text = text.lower()
            
            # 根据拼音、代码或名称进行过滤
            mask = (
                self.stock_df['pinyin'].str.contains(text, case=False) |  # 全拼匹配
                self.stock_df['pinyin_initials'].str.contains(text, case=False) |  # 首字母匹配
                self.stock_df['code'].str.contains(text, case=False) |  # 代码匹配
                self.stock_df['name'].str.contains(text, case=False)  # 名称匹配
            )
            filtered_stocks = self.stock_df[mask]
            
            # 更新下拉列表
            self.combo_box.clear()
            for _, row in filtered_stocks.iterrows():
                display_text = f"{row['code']} - {row['name']} ({row['pinyin_initials']})"
                self.combo_box.addItem(display_text, (row['code'], row['name']))

        except Exception as e:
            self.logger.error(f"过滤股票失败: {str(e)}")

    def on_stock_selected(self, index):
        """处理股票选择"""
        try:
            code, name = self.combo_box.itemData(index)
            self.stock_selected.emit(code, name)
            self.logger.info(f"选择股票: {code} - {name}")
        except Exception as e:
            self.logger.error(f"处理股票选择失败: {str(e)}")

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入股票代码、名称、拼音或首字母搜索...")
        self.search_input.textChanged.connect(self.on_text_changed)
        
        # 自动完成器
        self.completer = QCompleter([])
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.search_input.setCompleter(self.completer)
        
        # 下拉列表
        self.combo_box = QComboBox()
        self.combo_box.setMaxVisibleItems(10)
        self.combo_box.currentIndexChanged.connect(self.on_stock_selected)
        
        layout.addWidget(self.search_input)
        layout.addWidget(self.combo_box)
        
        self.setLayout(layout) 