# -*- encoding: UTF-8 -*-

import matplotlib.pyplot as plt
from matplotlib.dates import date2num, DateFormatter
from mplfinance.original_flavor import candlestick_ohlc
import logging
from PySide6.QtWidgets import QDialog, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
from logger_manager import LoggerManager

class StockChartDialog(QDialog):
    def __init__(self, code, name, data=None, signals=None, parent=None, logger_manager=None):
        super().__init__(parent)
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("stock_chart")
        
        # 设置窗口属性
        self.setWindowTitle(f"{code} - {name} 走势图")
        self.setModal(True)
        self.resize(1200, 800)
        
        # 创建StockChart实例
        self.chart = StockChart()
        
        # 创建布局
        layout = QVBoxLayout(self)
        self.canvas = FigureCanvas(self.chart.figure)
        layout.addWidget(self.canvas)
        
        # 绘制图表
        if data is not None:
            self.chart.plot_candlestick(data)
            if signals:
                self.chart.plot_signals(signals)
                
        # 刷新画布
        self.canvas.draw()

class StockChart:
    def __init__(self):
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 创建图表
        self.figure = plt.figure(figsize=(15, 10))
        
        # 设置子图布局参数
        self.figure.subplots_adjust(left=0.08, right=0.92, top=0.95, bottom=0.05, hspace=0.2)
        
        # 创建子图，使用GridSpec
        gs = self.figure.add_gridspec(4, 1, height_ratios=[3, 1, 1, 1])
        self.price_ax = self.figure.add_subplot(gs[0])
        self.volume_ax = self.figure.add_subplot(gs[1])
        self.signal_ax = self.figure.add_subplot(gs[2:])
        
        # 设置标题样式
        self.price_ax.set_title('股票走势图', fontsize=12, pad=15)
        
        # 定义策略样式
        self.strategy_styles = {
            'RARA策略': {'color': 'blue', 'marker': '^', 'base_size': 100},
            'Alpha101策略': {'color': 'red', 'marker': 'o', 'base_size': 100},
            'MACD策略': {'color': 'purple', 'marker': 's', 'base_size': 100},
            '默认策略': {'color': 'gray', 'marker': 'D', 'base_size': 100}
        }
        
    def plot_candlestick(self, data):
        """绘制K线图"""
        try:
            # 清除现有图形
            self.price_ax.clear()
            self.volume_ax.clear()
            self.signal_ax.clear()
            
            # 准备数据
            dates = data.index
            quotes = []
            for date, row in data.iterrows():
                quotes.append((date2num(date), row['开盘'], row['最高'], row['最低'], row['收盘']))
                
            # 绘制K线
            candlestick_ohlc(self.price_ax, quotes, width=0.6, colorup='red', colordown='green')
            
            # 设置x轴格式
            self.price_ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
            plt.setp(self.price_ax.get_xticklabels(), rotation=30)
            
            # 绘制成交量
            self.volume_ax.bar(dates, data['成交量'], color='blue', alpha=0.5)
            self.volume_ax.set_ylabel('成交量')
            
            # 设置网格
            self.price_ax.grid(True, linestyle='--', alpha=0.3)
            self.volume_ax.grid(True, linestyle='--', alpha=0.3)
            self.signal_ax.grid(True, linestyle='--', alpha=0.3)
            
            # 设置标签
            self.price_ax.set_ylabel('价格')
            self.volume_ax.set_ylabel('成交量')
            
        except Exception as e:
            logging.error(f"绘制K线图失败: {str(e)}")
            
    def plot_signals(self, signals):
        """绘制交易信号"""
        try:
            if not signals:
                return
                
            # 清除现有信号
            self.signal_ax.clear()
            
            # 按策略分组信号
            strategy_signals = {}
            for signal in signals:
                strategy = signal.get('strategy', '默认策略')
                if strategy not in strategy_signals:
                    strategy_signals[strategy] = []
                strategy_signals[strategy].append(signal)
                
            # 为每个策略绘制信号
            for strategy, strat_signals in strategy_signals.items():
                style = self.strategy_styles.get(strategy, self.strategy_styles['默认策略'])
                
                buy_dates = []
                buy_prices = []
                sell_dates = []
                sell_prices = []
                buy_strengths = []
                sell_strengths = []
                
                for signal in strat_signals:
                    date = signal['date']
                    price = signal['price']
                    strength = signal.get('strength', 1)
                    
                    if signal['type'] == '买入':
                        buy_dates.append(date)
                        buy_prices.append(price)
                        buy_strengths.append(strength)
                    else:
                        sell_dates.append(date)
                        sell_prices.append(price)
                        sell_strengths.append(strength)
                        
                # 绘制买入信号
                if buy_dates:
                    sizes = [style['base_size'] * (1 + 0.2 * s) for s in buy_strengths]
                    self.price_ax.scatter(buy_dates, buy_prices, 
                                        color=style['color'], marker=style['marker'],
                                        s=sizes, alpha=0.7, label=f"{strategy}买入")
                    self.signal_ax.scatter(buy_dates, [1] * len(buy_dates),
                                         color=style['color'], marker=style['marker'],
                                         s=sizes, alpha=0.7)
                                         
                # 绘制卖出信号
                if sell_dates:
                    sizes = [style['base_size'] * (1 + 0.2 * s) for s in sell_strengths]
                    self.price_ax.scatter(sell_dates, sell_prices,
                                        color=style['color'], marker=style['marker'],
                                        s=sizes, alpha=0.7, label=f"{strategy}卖出")
                    self.signal_ax.scatter(sell_dates, [0] * len(sell_dates),
                                         color=style['color'], marker=style['marker'],
                                         s=sizes, alpha=0.7)
                                         
            # 设置信号区域的y轴
            self.signal_ax.set_ylim(-0.5, 1.5)
            self.signal_ax.set_yticks([0, 1])
            self.signal_ax.set_yticklabels(['卖出', '买入'])
            self.signal_ax.set_title('交易信号')
            
            # 添加图例，放在图表外部右侧
            box = self.price_ax.get_position()
            self.price_ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
            handles, labels = self.price_ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            self.price_ax.legend(by_label.values(), by_label.keys(),
                               loc='center left', bbox_to_anchor=(1.01, 0.5))
            
        except Exception as e:
            logging.error(f"绘制交易信号失败: {str(e)}")
            
    def show(self):
        """显示图表"""
        plt.show()
        
    def save(self, filename):
        """保存图表"""
        try:
            self.figure.savefig(filename, bbox_inches='tight', dpi=300)
        except Exception as e:
            logging.error(f"保存图表失败: {str(e)}")

def show_stock_chart(code, name, data=None, signals=None, parent=None, logger_manager=None):
    """显示股票走势图的便捷函数"""
    dialog = StockChartDialog(code, name, data, signals, parent, logger_manager)
    dialog.exec_()