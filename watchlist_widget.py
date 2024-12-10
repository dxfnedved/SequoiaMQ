from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal
import pandas as pd
from logger_manager import LoggerManager
from data_fetcher import DataFetcher

class WatchlistWidget(QWidget):
    """自选股列表组件"""
    stock_double_clicked = Signal(str, str)  # 股票代码, 股票名称
    analyze_stocks = Signal(list)  # 要分析的股票列表 [(code, name), ...]

    def __init__(self, parent=None, logger_manager=None):
        super().__init__(parent)
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("watchlist")
        
        # 初始化数据获取器
        self.data_fetcher = DataFetcher(logger_manager)
        
        # 初始化定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stock_data)
        self.update_timer.setInterval(15000)  # 15秒更新一次
        
        self.init_ui()
        self.load_watchlist()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 按钮工具栏
        toolbar = QHBoxLayout()
        
        self.analyze_btn = QPushButton("分析选中")
        self.analyze_btn.clicked.connect(self.analyze_selected)
        toolbar.addWidget(self.analyze_btn)
        
        self.delete_btn = QPushButton("删除选中")
        self.delete_btn.clicked.connect(self.delete_selected)
        toolbar.addWidget(self.delete_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 自选股表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "选择", "代码", "名称", "现价", "涨跌幅", "换手率", "操作"
        ])
        
        # 设置表格样式
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
    def load_watchlist(self):
        """加载自选股列表"""
        try:
            # 从文件加载自选股列表
            self.watchlist_df = pd.read_json('data/watchlist.json')
            self.update_table()
            self.update_timer.start()
            
        except Exception as e:
            self.logger.error(f"加载自选股列表失败: {str(e)}")
            self.watchlist_df = pd.DataFrame(columns=['code', 'name'])
            
    def save_watchlist(self):
        """保存自选股列表"""
        try:
            self.watchlist_df.to_json('data/watchlist.json', orient='records', force_ascii=False)
            self.logger.info("保存自选股列表成功")
        except Exception as e:
            self.logger.error(f"保存自选股列表失败: {str(e)}")
            
    def add_stock(self, code, name):
        """添加自选股"""
        try:
            if code not in self.watchlist_df['code'].values:
                self.watchlist_df = pd.concat([
                    self.watchlist_df,
                    pd.DataFrame({'code': [code], 'name': [name]})
                ], ignore_index=True)
                self.save_watchlist()
                self.update_table()
                self.logger.info(f"添加自选股成功: {code} - {name}")
            else:
                self.logger.warning(f"股票已在自选股列表中: {code} - {name}")
                
        except Exception as e:
            self.logger.error(f"添加自选股失败: {str(e)}")
            
    def delete_selected(self):
        """删除选中的自选股"""
        try:
            to_delete = []
            for row in range(self.table.rowCount()):
                checkbox = self.table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    code = self.table.item(row, 1).text()
                    to_delete.append(code)
                    
            if not to_delete:
                return
                
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除选中的 {len(to_delete)} 只股票吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.watchlist_df = self.watchlist_df[
                    ~self.watchlist_df['code'].isin(to_delete)
                ]
                self.save_watchlist()
                self.update_table()
                self.logger.info(f"删除自选股成功: {to_delete}")
                
        except Exception as e:
            self.logger.error(f"删除自选股失败: {str(e)}")
            
    def analyze_selected(self):
        """��析选中的自选股"""
        try:
            to_analyze = []
            for row in range(self.table.rowCount()):
                checkbox = self.table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    code = self.table.item(row, 1).text()
                    name = self.table.item(row, 2).text()
                    to_analyze.append((code, name))
                    
            if not to_analyze:
                QMessageBox.warning(self, "提示", "请先选择要分析的股票")
                return
                
            self.analyze_stocks.emit(to_analyze)
            self.logger.info(f"开始分析股票: {to_analyze}")
            
        except Exception as e:
            self.logger.error(f"分析股票失败: {str(e)}")
            
    def update_stock_data(self):
        """更新股票数据"""
        try:
            if self.watchlist_df.empty:
                return
                
            # 获取实时数据
            codes = self.watchlist_df['code'].tolist()
            data = self.data_fetcher.fetch_realtime_data(codes)
            
            # 更新表格
            for row in range(self.table.rowCount()):
                code = self.table.item(row, 1).text()
                if code in data:
                    stock_data = data[code]
                    
                    # 更新现价
                    price_item = QTableWidgetItem(f"{stock_data['price']:.2f}")
                    self.table.setItem(row, 3, price_item)
                    
                    # 更新涨跌幅
                    change = stock_data['change']
                    change_item = QTableWidgetItem(f"{change:.2f}%")
                    change_item.setForeground(
                        Qt.red if change > 0 else Qt.green if change < 0 else Qt.black
                    )
                    self.table.setItem(row, 4, change_item)
                    
                    # 更新换手率
                    turnover = stock_data['turnover']
                    turnover_item = QTableWidgetItem(f"{turnover:.2f}%")
                    self.table.setItem(row, 5, turnover_item)
                    
        except Exception as e:
            self.logger.error(f"更新股票数据失败: {str(e)}")
            
    def update_table(self):
        """更新表格显示"""
        try:
            self.table.setRowCount(len(self.watchlist_df))
            
            for row, (_, stock) in enumerate(self.watchlist_df.iterrows()):
                # 选择框
                checkbox = QCheckBox()
                self.table.setCellWidget(row, 0, checkbox)
                
                # 代码
                code_item = QTableWidgetItem(stock['code'])
                self.table.setItem(row, 1, code_item)
                
                # 名称
                name_item = QTableWidgetItem(stock['name'])
                self.table.setItem(row, 2, name_item)
                
                # 现价、涨跌幅、换手率先设为空
                for col in range(3, 6):
                    self.table.setItem(row, col, QTableWidgetItem("--"))
                    
                # 操作按钮
                btn_layout = QHBoxLayout()
                analyze_btn = QPushButton("分析")
                analyze_btn.clicked.connect(
                    lambda c=stock['code'], n=stock['name']: 
                    self.analyze_stocks.emit([(c, n)])
                )
                delete_btn = QPushButton("删除")
                delete_btn.clicked.connect(
                    lambda c=stock['code']: self.delete_stock(c)
                )
                btn_layout.addWidget(analyze_btn)
                btn_layout.addWidget(delete_btn)
                
                btn_widget = QWidget()
                btn_widget.setLayout(btn_layout)
                self.table.setCellWidget(row, 6, btn_widget)
                
            # 立即更新数据
            self.update_stock_data()
            
        except Exception as e:
            self.logger.error(f"更新表格显示失败: {str(e)}")
            
    def delete_stock(self, code):
        """删除单个自选股"""
        try:
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除股票 {code} 吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.watchlist_df = self.watchlist_df[
                    self.watchlist_df['code'] != code
                ]
                self.save_watchlist()
                self.update_table()
                self.logger.info(f"删除自选股成功: {code}")
                
        except Exception as e:
            self.logger.error(f"删除自选股失败: {str(e)}")
            
    def on_item_double_clicked(self, item):
        """处理双击事件"""
        try:
            row = item.row()
            code = self.table.item(row, 1).text()
            name = self.table.item(row, 2).text()
            self.stock_double_clicked.emit(code, name)
            self.logger.info(f"双击股票: {code} - {name}")
        except Exception as e:
            self.logger.error(f"处理双击事件���败: {str(e)}")
            
    def closeEvent(self, event):
        """关闭事件"""
        self.update_timer.stop()
        super().closeEvent(event) 