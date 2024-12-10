# -*- encoding: UTF-8 -*-

import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import numpy as np
from datetime import datetime
import os
from PySide6.QtWidgets import QDialog, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from logger_manager import LoggerManager

class StockChartDialog(QDialog):
    """股票图表对话框"""
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
        
        # 创建图表
        if data is not None:
            filepath = self.chart.plot_stock(data, code, name, signals)
            if filepath:
                # 显示图表
                fig = plt.figure(figsize=(15, 10))
                canvas = FigureCanvas(fig)
                layout.addWidget(canvas)
                img = plt.imread(filepath)
                plt.imshow(img)
                plt.axis('off')
                canvas.draw()

class StockChart:
    def __init__(self, save_dir='charts'):
        self.save_dir = save_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 定义策略标记样式
        self.strategy_styles = {
            'Alpha101策略': {'color': 'red', 'marker': 'o', 'base_size': 100},
            'RSRS策略': {'color': 'blue', 'marker': '^', 'base_size': 100},
            'Turtle策略': {'color': 'green', 'marker': 's', 'base_size': 100},
            'LowATR策略': {'color': 'purple', 'marker': 'D', 'base_size': 100}
        }
        
    def plot_stock(self, data, code, name, signals=None):
        """
        绘制股票K线图和信号
        :param data: DataFrame 股票数据
        :param code: str 股票代码
        :param name: str 股票名称
        :param signals: list 信号列表，每个信号是(策略名, 信号类型, 时间)的元组
        """
        try:
            # 准备数据
            df = data.copy()
            df.index = pd.to_datetime(df.index)
            
            # 创建图表
            fig, axes = mpf.plot(df, type='candle', style='charles',
                               volume=True, returnfig=True,
                               title=f'{code} {name} 分析图',
                               figsize=(15, 10))
                               
            # 如果有信号，添加到图表上
            if signals:
                ax = axes[0]  # 主图
                for strategy, signal_type, signal_time in signals:
                    if strategy in self.strategy_styles:
                        style = self.strategy_styles[strategy]
                        
                        # 获取信号点的y坐标（价格）
                        price = df.loc[signal_time, 'Close']
                        
                        # 根据信号类型调整标记
                        if '买入' in signal_type or '看多' in signal_type:
                            marker = '^'  # 上三角
                            color = 'red'
                            y_offset = -0.02  # 向下偏移
                        elif '卖出' in signal_type or '看空' in signal_type:
                            marker = 'v'  # 下三角
                            color = 'green'
                            y_offset = 0.02  # 向上偏移
                        else:
                            marker = style['marker']
                            color = style['color']
                            y_offset = 0
                            
                        # 绘制标记
                        ax.scatter(signal_time, price * (1 + y_offset),
                                 color=color, marker=marker,
                                 s=style['base_size'], alpha=0.6,
                                 label=f'{strategy}_{signal_type}')
                                 
            # 添加图例
            ax.legend()
            
            # 保存图表
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{code}_{timestamp}.png'
            filepath = os.path.join(self.save_dir, filename)
            plt.savefig(filepath)
            plt.close()
            
            return filepath
            
        except Exception as e:
            print(f"绘制股票图表失败: {str(e)}")
            return None

def show_stock_chart(code, name, data=None, signals=None, parent=None, logger_manager=None):
    """显示股票走势图的便捷函数"""
    dialog = StockChartDialog(code, name, data, signals, parent, logger_manager)
    dialog.exec_()