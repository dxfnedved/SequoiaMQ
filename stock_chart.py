from PySide6.QtWidgets import QWidget, QVBoxLayout, QDialog, QMessageBox
from PySide6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import mplfinance as mpf
import matplotlib
import os
import platform
import traceback
from logger_manager import LoggerManager

class StockChartDialog(QDialog):
    """股票走势图对话框"""
    def __init__(self, code, name, data=None, signals=None, parent=None, logger_manager=None):
        super().__init__(parent)
        self.code = code
        self.name = name
        self.data = data
        self.signals = signals or []
        
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("stock_chart")
        
        self.setWindowTitle(f"{code} - {name} 走势图")
        self.setModal(True)
        self.resize(1200, 800)
        
        self.setup_font()
        self.init_ui()
        
        # 如果没有提供数据，则尝试加载
        if self.data is None:
            if not self.load_data():
                self.logger.error(f"无法加载股票{code}数据")
                QMessageBox.warning(self, "警告", "无法加载股票数据")
                return
        else:
            # 处理提供的数据
            if not self.prepare_data():
                self.logger.error(f"处理股票{code}数据失败")
                QMessageBox.warning(self, "警告", "数据格式错误")
                return
            
        self.plot_chart()

    def setup_font(self):
        """设置中文字体"""
        if platform.system() == "Windows":
            matplotlib.rc("font", family="Microsoft YaHei")
        else:
            matplotlib.rc("font", family="WenQuanYi Micro Hei")
        matplotlib.rcParams['axes.unicode_minus'] = False

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建图表
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: none;
            }
        """)

    def load_data(self):
        """加载股票数据"""
        try:
            # 计算日期范围（最近三个月）
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            # 获取日线数据
            self.data = ak.stock_zh_a_hist(
                symbol=self.code,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d'),
                adjust='qfq'
            )
            
            if self.data is None or self.data.empty:
                return False
            
            # 重命名列以适配mplfinance
            self.data = self.data.rename(columns={
                '日期': 'Date',
                '开盘': 'Open',
                '最高': 'High',
                '最低': 'Low',
                '收盘': 'Close',
                '成交量': 'Volume'
            })
            
            # 确保数据类型正确
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in numeric_columns:
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
            
            self.data.set_index('Date', inplace=True)
            self.data.index = pd.to_datetime(self.data.index)
            
            return True
            
        except Exception as e:
            self.logger.error(f"加载股票数据失败: {str(e)}\n{traceback.format_exc()}")
            return False

    def prepare_data(self):
        """处理数据格式"""
        try:
            # 创建新的DataFrame以避免修改原始数据
            self.plot_data = self.data.copy()
            
            # 确保索引是datetime类型
            if not isinstance(self.plot_data.index, pd.DatetimeIndex):
                if '日期' in self.plot_data.columns:
                    self.plot_data.set_index('日期', inplace=True)
                self.plot_data.index = pd.to_datetime(self.plot_data.index)
            
            # 重命名列以适配mplfinance
            column_mapping = {
                '开盘': 'Open',
                '最高': 'High',
                '最低': 'Low',
                '收盘': 'Close',
                '成交量': 'Volume'
            }
            
            # 重命名列
            self.plot_data = self.plot_data.rename(columns=column_mapping)
            
            # 确保数据类型正确
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in numeric_columns:
                if col in self.plot_data.columns:
                    self.plot_data[col] = pd.to_numeric(self.plot_data[col], errors='coerce')
            
            # 确保所有必要的列都存在
            missing_cols = [col for col in numeric_columns if col not in self.plot_data.columns]
            if missing_cols:
                self.logger.error(f"缺少必要的列: {missing_cols}")
                return False
            
            # 删除包含NaN的行
            self.plot_data = self.plot_data.dropna(subset=numeric_columns)
            
            # 确保数据按日期排序
            self.plot_data = self.plot_data.sort_index()
            
            # 确保至少有一些数据点
            if len(self.plot_data) < 5:
                self.logger.error("数据点太少，无法绘制图表")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"处理数据失败: {str(e)}\n{traceback.format_exc()}")
            return False

    def plot_chart(self):
        """绘制走势图"""
        try:
            if not hasattr(self, 'plot_data') or self.plot_data is None or self.plot_data.empty:
                self.logger.error("没有可用的数据来绘制图表")
                QMessageBox.warning(self, "警告", "没有可用的数据来绘制图表")
                return
            
            # 清除现有图表
            self.figure.clear()
            
            # 创建子图
            gs = self.figure.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.1)
            ax1 = self.figure.add_subplot(gs[0])
            ax2 = self.figure.add_subplot(gs[1])
            
            # 设置K线图样式
            mc = mpf.make_marketcolors(
                up='red',
                down='green',
                edge='inherit',
                wick='inherit',
                volume='in',
                ohlc='inherit'
            )
            s = mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle='--',
                y_on_right=False,
                rc={'font.family': matplotlib.rcParams['font.family']}
            )
            
            # 添加均线
            ma5 = self.plot_data['Close'].rolling(window=5, min_periods=1).mean()
            ma10 = self.plot_data['Close'].rolling(window=10, min_periods=1).mean()
            ma20 = self.plot_data['Close'].rolling(window=20, min_periods=1).mean()
            
            apds = [
                mpf.make_addplot(ma5, ax=ax1, color='#1976D2', width=1, label='MA5'),
                mpf.make_addplot(ma10, ax=ax1, color='#FB8C00', width=1, label='MA10'),
                mpf.make_addplot(ma20, ax=ax1, color='#7B1FA2', width=1, label='MA20')
            ]
            
            # 绘制K线图
            mpf.plot(
                self.plot_data,
                type='candle',
                style=s,
                addplot=apds,
                ax=ax1,
                volume=ax2,
                title=f'{self.code} - {self.name} 走势图',
                ylabel='价格',
                ylabel_lower='成交量',
                warn_too_much_data=len(self.plot_data) + 100,  # 避免数据过多的警告
                show_nontrading=False
            )
            
            # 标记买入卖出点
            for signal in self.signals:
                try:
                    date = pd.to_datetime(signal.get('date'))
                    if date in self.plot_data.index:
                        if signal.get('type') == '买入':
                            ax1.plot(date, self.plot_data.loc[date, 'Low'] * 0.99, '^', 
                                    color='#D32F2F', markersize=12, label=f"买入({signal.get('strategy', '')})")
                        elif signal.get('type') == '卖出':
                            ax1.plot(date, self.plot_data.loc[date, 'High'] * 1.01, 'v',
                                    color='#388E3C', markersize=12, label=f"卖出({signal.get('strategy', '')})")
                except Exception as e:
                    self.logger.warning(f"标记信号点失败: {str(e)}")
                    continue
            
            # 添加图例
            handles, labels = ax1.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax1.legend(by_label.values(), by_label.keys(),
                      loc='upper left', frameon=True, fancybox=True, framealpha=0.9,
                      fontsize=10, bbox_to_anchor=(0.01, 0.99))
            
            # 设置���格
            ax1.grid(True, linestyle='--', alpha=0.3)
            ax2.grid(True, linestyle='--', alpha=0.3)
            
            # 调整布局
            self.figure.tight_layout()
            
            # 刷新画布
            self.canvas.draw()
            
        except Exception as e:
            self.logger.error(f"绘制图表失败: {str(e)}\n{traceback.format_exc()}")
            QMessageBox.warning(self, "警告", f"绘制图表失败：{str(e)}")

def show_stock_chart(code, name, data=None, signals=None, parent=None, logger_manager=None):
    """显示股票走势图的便捷函数"""
    dialog = StockChartDialog(code, name, data, signals, parent, logger_manager)
    dialog.exec_() 