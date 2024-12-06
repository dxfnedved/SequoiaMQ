from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                               QTextEdit, QMessageBox, QLabel, QHBoxLayout)
from PySide6.QtCore import Qt
import pandas as pd
import sys
import logging
import work_flow
import data_fetcher
import akshare as ak
import os
from datetime import datetime

class StockSelector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("股票策略分析器")
        self.setGeometry(100, 100, 1000, 800)
        
        # 确保results目录存在
        self.results_dir = 'results'
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            
        # 创建日志目录
        self.log_dir = os.path.join(self.results_dir, 'logs')
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # 设置文件日志
        self.setup_logging()
        
        # 创建中心部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建说明标签
        instruction_label = QLabel(
            "使用说明：\n"
            "1. 在下方输入框中输入股票代码，每行一个\n"
            "2. 股票代码格式：沪市以6开头，深市以0或3开头\n"
            "3. 点击'开始分析'按钮进行策略分析\n"
            "4. 分析结果将在下方表格中显示"
        )
        instruction_label.setStyleSheet("font-size: 12px; color: #666;")
        
        # 创建输入区域
        input_layout = QHBoxLayout()
        
        # 创建文本输入框
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("请输入股票代码，每行一个\n例如：\n600000\n000001\n300750")
        self.text_edit.setMaximumHeight(150)
        
        # 创建按钮区域
        button_layout = QVBoxLayout()
        analyze_btn = QPushButton("开始分析")
        analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        clear_btn = QPushButton("清空")
        clear_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)
        
        button_layout.addWidget(analyze_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        
        input_layout.addWidget(self.text_edit, stretch=4)
        input_layout.addLayout(button_layout, stretch=1)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["股票代码", "股票名称", "分析结果"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                alternate-background-color: #f6f6f6;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        self.table.setAlternatingRowColors(True)
        
        # 添加部件到布局
        layout.addWidget(instruction_label)
        layout.addLayout(input_layout)
        layout.addWidget(self.table)
        
        # 连接信号
        analyze_btn.clicked.connect(self.analyze_stocks)
        clear_btn.clicked.connect(self.text_edit.clear)
        
        self.stocks = []

    def setup_logging(self):
        """设置日志"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(self.log_dir, f'analysis_{timestamp}.log')
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        
        logger = logging.getLogger()
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)

    def get_stock_name(self, code):
        """获取股票名称"""
        try:
            stock_info = ak.stock_individual_info_em(symbol=code)
            if not stock_info.empty:
                return stock_info.iloc[0]['股票简称']
        except:
            pass
        return "未知"

    def export_results(self, results, stocks_data):
        """导出分析结果到CSV文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 准备导出数据
            export_data = []
            for code, name in self.stocks:
                data = {
                    '股票代码': code,
                    '股票名称': name,
                    '分析日期': timestamp[:8],
                    '分析时间': timestamp[9:],
                }
                
                # 添加策略分析结果
                if code in results:
                    strategy_names = [s[0] for s in results[code] if s[1] == "买入"]
                    data.update({
                        '分析结果': "触发买入信号" if strategy_names else "无买入信号",
                        '触发策略数': len(strategy_names),
                        '触发策略': ', '.join(strategy_names) if strategy_names else '无',
                    })
                else:
                    data.update({
                        '分析结果': "分析失败",
                        '触发策略数': 0,
                        '触发策略': '无',
                    })
                
                # 添加最新行情数据
                if code in stocks_data:
                    stock_data = stocks_data[code].iloc[-1]
                    data.update({
                        '最新价': stock_data['收盘'],
                        '涨跌幅': f"{stock_data['p_change']:.2f}%",
                        '成交量': stock_data['成交量'],
                        '成交额': stock_data['成交量'] * stock_data['收盘'],
                    })
                else:
                    data.update({
                        '最新价': '-',
                        '涨跌幅': '-',
                        '成交量': '-',
                        '成交额': '-',
                    })
                
                export_data.append(data)
            
            # 创建DataFrame并导出
            df = pd.DataFrame(export_data)
            
            # 设置列顺序
            columns = [
                '股票代码', '股票名称', '分析日期', '分析时间', 
                '分析结果', '触发策略数', '触发策略',
                '最新价', '涨跌幅', '成交量', '成交额'
            ]
            df = df[columns]
            
            # 导出到CSV
            filename = f'stock_analysis_{timestamp}.csv'
            filepath = os.path.join(self.results_dir, filename)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            # 记录日志
            logging.info(f"分析结果已导出到: {filepath}")
            logging.info(f"分析股票数: {len(self.stocks)}")
            logging.info(f"触发入信号数: {sum(1 for d in export_data if d['分析结果'] == '触发买入信号')}")
            
            return filepath
            
        except Exception as e:
            logging.error(f"导出结果时出错: {str(e)}")
            raise

    def analyze_stocks(self):
        """分析输入的股票"""
        # 获取输入的股票代码
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请输入股票代码")
            return
            
        # 处理输入的股票代码
        codes = [code.strip() for code in text.split('\n') if code.strip()]
        
        # 验证股票代码格式
        invalid_codes = [code for code in codes if not (
            (code.startswith('6') and len(code) == 6) or 
            (code.startswith(('0', '3')) and len(code) == 6)
        )]
        
        if invalid_codes:
            QMessageBox.warning(self, "警告", f"以下股票代码格式错误：\n{', '.join(invalid_codes)}")
            return
            
        self.stocks = []
        self.table.setRowCount(len(codes))
        
        # 获取股票名称并构建股票列表
        for i, code in enumerate(codes):
            # 更新表格显示状态
            self.table.setItem(i, 0, QTableWidgetItem(code))
            self.table.setItem(i, 1, QTableWidgetItem("获取中..."))
            self.table.setItem(i, 2, QTableWidgetItem("等待分析"))
            QApplication.processEvents()  # 更新界面
            
            try:
                name = self.get_stock_name(code)
                self.stocks.append((code, name))
                self.table.setItem(i, 1, QTableWidgetItem(name))
            except Exception as e:
                logging.error(f"获取股票{code}名称时出错：{str(e)}")
                self.table.setItem(i, 1, QTableWidgetItem("获取失败"))
            
        try:
            # 更新状态
            for i in range(self.table.rowCount()):
                self.table.setItem(i, 2, QTableWidgetItem("正在获取数据..."))
                QApplication.processEvents()
            
            # 获取股票数据
            stocks_data = data_fetcher.run(self.stocks)
            
            # 更新状态
            for i in range(self.table.rowCount()):
                self.table.setItem(i, 2, QTableWidgetItem("正在分析..."))
                QApplication.processEvents()
            
            # 运行策略分析
            strategies = {
                '放量上涨': work_flow.enter.check_volume,
                '均线多头': work_flow.keep_increasing.check,
                '停机坪': work_flow.parking_apron.check,
                '回踩年线': work_flow.backtrace_ma250.check,
                '无大幅回撤': work_flow.low_backtrace_increase.check,
                '海龟交易法则': work_flow.turtle_trade.check_enter,
                '高而窄的旗形': work_flow.high_tight_flag.check,
                '放量跌停': work_flow.climax_limitdown.check,
                'RARA策略': work_flow.RARA.check,
                'Alpha因子策略': work_flow.formulaic_alphas.check,
            }
            
            results = {}
            total_strategies = len(strategies)
            
            # 对每个股票进行策略分析
            for code, data in stocks_data.items():
                results[code] = []
                for idx, (strategy_name, strategy_func) in enumerate(strategies.items(), 1):
                    # 更新分析进度
                    row = next(i for i, (c, _) in enumerate(self.stocks) if c == code)
                    self.table.setItem(row, 2, QTableWidgetItem(f"分析中 ({idx}/{total_strategies})"))
                    QApplication.processEvents()
                    
                    try:
                        if strategy_func(code, data):
                            results[code].append((strategy_name, "买入"))
                    except Exception as e:
                        logging.error(f"策略{strategy_name}处理股票{code}时出错：{str(e)}")
            
            # 更新表格显示结果
            for i, (code, name) in enumerate(self.stocks):
                if code in results:
                    strategy_names = [s[0] for s in results[code] if s[1] == "买入"]
                    if strategy_names:
                        status = f"触发策略: {', '.join(strategy_names)}"
                        item = QTableWidgetItem(status)
                        item.setBackground(Qt.green)
                    else:
                        status = "无买入信号"
                        item = QTableWidgetItem(status)
                        item.setBackground(Qt.white)
                else:
                    status = "分析失败"
                    item = QTableWidgetItem(status)
                    item.setBackground(Qt.red)
                self.table.setItem(i, 2, item)
            
            # 导出结果
            try:
                filepath = self.export_results(results, stocks_data)
                QMessageBox.information(
                    self, 
                    "完成", 
                    f"分析完成！\n结果已导出到：\n{filepath}\n\n"
                    f"分析股票数：{len(self.stocks)}\n"
                    f"触发买入信号数：{sum(1 for c in results if results[c] and any(s[1] == '买入' for s in results[c]))}"
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "警告",
                    f"分析完成，但导出结果失败：{str(e)}"
                )
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"分析过程出错: {str(e)}")
            logging.error(f"分析过程出错: {str(e)}")
            # 更新失败状态
            for i in range(self.table.rowCount()):
                if self.table.item(i, 2).text() in ["正在获取数据...", "正在分析...", "等待分析"]:
                    self.table.setItem(i, 2, QTableWidgetItem("分析失败"))

def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    window = StockSelector()
    window.show()
    sys.exit(app.exec_()) 