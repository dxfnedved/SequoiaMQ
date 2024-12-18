"""Strategy selector widget implementation."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QSpinBox, QDoubleSpinBox, QFormLayout
)
from PySide6.QtCore import Signal, Qt
import json
import os
from logger_manager import LoggerManager

class StrategySelector(QWidget):
    """策略选择器组件"""
    strategies_changed = Signal(list)  # 策略列表变化信号
    
    def __init__(self, logger_manager=None, parent=None):
        super().__init__(parent)
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("strategy_selector")
        
        self.settings_file = 'data/strategy_settings.json'
        os.makedirs('data', exist_ok=True)
        
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        
        # 左侧策略列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.strategy_list = QListWidget()
        self.strategy_list.itemSelectionChanged.connect(self.on_strategy_selected)
        left_layout.addWidget(self.strategy_list)
        
        # 添加策略
        self.add_strategy_item("RSRS策略", "RSRS_Strategy")
        self.add_strategy_item("海龟交易策略", "TurtleStrategy")
        self.add_strategy_item("Alpha101策略", "Alpha101Strategy")
        self.add_strategy_item("低波动策略", "LowATRStrategy")
        self.add_strategy_item("低回撤增长策略", "LowBacktraceStrategy")
        self.add_strategy_item("持续上涨策略", "KeepIncreasingStrategy")
        self.add_strategy_item("回踩年线策略", "BacktraceMA250Strategy")
        
        layout.addWidget(left_panel)
        
        # 右侧参数设置
        right_panel = QWidget()
        self.right_layout = QFormLayout(right_panel)
        layout.addWidget(right_panel)
        
    def add_strategy_item(self, name, strategy_id):
        """添加策略项"""
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, strategy_id)
        self.strategy_list.addItem(item)
        
    def load_settings(self):
        """加载策略设置"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                # 设置选中状态
                for i in range(self.strategy_list.count()):
                    item = self.strategy_list.item(i)
                    strategy_id = item.data(Qt.UserRole)
                    if strategy_id in settings:
                        item.setSelected(True)
                        
                self.logger.info("加载策略设置成功")
                
        except Exception as e:
            self.logger.error(f"加载策略设置失败: {str(e)}")
            
    def save_settings(self):
        """保存策略设置"""
        try:
            settings = {}
            for i in range(self.strategy_list.count()):
                item = self.strategy_list.item(i)
                if item.isSelected():
                    strategy_id = item.data(Qt.UserRole)
                    settings[strategy_id] = {}
                    
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
                
            self.logger.info("保存策略设置成功")
            
        except Exception as e:
            self.logger.error(f"保存策略设置失败: {str(e)}")
            
    def get_selected_strategies(self):
        """获取选中的策略"""
        strategies = []
        for i in range(self.strategy_list.count()):
            item = self.strategy_list.item(i)
            if item.isSelected():
                strategy_id = item.data(Qt.UserRole)
                strategies.append(strategy_id)
        return strategies
        
    def on_strategy_selected(self):
        """处理策略选择变化"""
        try:
            # 清除参数设置
            while self.right_layout.count():
                item = self.right_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                    
            # 获取选中的策略
            selected = self.strategy_list.selectedItems()
            if not selected:
                return
                
            # 添加参数设置
            strategy_id = selected[0].data(Qt.UserRole)
            if strategy_id == "RSRS_Strategy":
                self.add_rsrs_params()
            elif strategy_id == "TurtleStrategy":
                self.add_turtle_params()
            elif strategy_id == "Alpha101Strategy":
                self.add_alpha101_params()
                
            # 保存设置并发送信号
            self.save_settings()
            self.strategies_changed.emit(self.get_selected_strategies())
            
        except Exception as e:
            self.logger.error(f"处理策略选择变化失败: {str(e)}")
            
    def add_rsrs_params(self):
        """添加RSRS策略参数"""
        self.right_layout.addRow("N日时间窗口:", QSpinBox())
        self.right_layout.addRow("M日标准化窗口:", QSpinBox())
        self.right_layout.addRow("买入阈值:", QDoubleSpinBox())
        self.right_layout.addRow("卖出阈值:", QDoubleSpinBox())
        
    def add_turtle_params(self):
        """添加海龟交易策略参数"""
        self.right_layout.addRow("入场周期:", QSpinBox())
        self.right_layout.addRow("退出周期:", QSpinBox())
        self.right_layout.addRow("ATR周期:", QSpinBox())
        
    def add_alpha101_params(self):
        """添加Alpha101策略参数"""
        self.right_layout.addRow("Alpha因子:", QSpinBox()) 