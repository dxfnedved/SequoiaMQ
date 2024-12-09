import matplotlib.pyplot as plt
import mplfinance as mpf
from PySide6.QtWidgets import QDialog, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd
from logger_manager import LoggerManager
import matplotlib as mpl

class StockChartDialog(QDialog):
    """股票图表对话框"""
    def __init__(self, code, name, data=None, signals=None, parent=None, logger_manager=None):
        super().__init__(parent)
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("stock_chart")
        
        # 配置中文字体
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        self.code = code
        self.name = name
        self.plot_data = data
        self.signals = signals or []
        
        self.init_ui()
        self.plot_chart()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"{self.code} - {self.name} 走势图")
        self.setModal(True)
        self.resize(1200, 800)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 创建图表
        self.figure = plt.figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        
    def plot_chart(self):
        """绘制走势图"""
        try:
            if not self.plot_data or self.plot_data.empty:
                self.logger.error("没有可用的数据来绘制图表")
                return
            
            # 清除现有图表
            self.figure.clear()
            
            # 创建子图
            gs = self.figure.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.1)
            ax1 = self.figure.add_subplot(gs[0])
            ax2 = self.figure.add_subplot(gs[1])
            
            # 设置标题
            ax1.set_title(f'{self.code} - {self.name} 走势图', pad=20, fontproperties='Microsoft YaHei')
            
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
                rc={
                    'font.family': 'Microsoft YaHei'
                }
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
                ylabel='价格',
                ylabel_lower='成交量',
                warn_too_much_data=len(self.plot_data) + 100,
                show_nontrading=False,
                tight_layout=True
            )
            
            # 标记买入卖出点
            if self.signals:
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
            
            # 设置网格
            ax1.grid(True, linestyle='--', alpha=0.3)
            ax2.grid(True, linestyle='--', alpha=0.3)
            
            # 调整布局
            self.figure.tight_layout()
            
            # 刷新画布
            self.canvas.draw()
            
        except Exception as e:
            self.logger.error(f"绘制图表失败: {str(e)}")
            raise

def show_stock_chart(code, name, data=None, signals=None, parent=None, logger_manager=None):
    """显示股票走势图的便捷函数"""
    dialog = StockChartDialog(code, name, data, signals, parent, logger_manager)
    dialog.exec_()