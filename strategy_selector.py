from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QListWidget, QListWidgetItem, QLabel, QFileDialog)
from PySide6.QtCore import Qt
import json
import os
from logger_manager import LoggerManager
import importlib
import pkgutil
import strategy

class StrategySelector(QDialog):
    """策略选择对话框"""
    def __init__(self, parent=None, logger_manager=None):
        super().__init__(parent)
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("strategy_selector")
        
        # 初始化策略列表
        self.strategies = {}
        self.load_strategies()
        
        # 加载已保存的策略选择
        self.selected_strategies = []
        self.load_strategy_template()
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("策略选择")
        self.setModal(True)
        self.resize(400, 500)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("选择要使用的策略")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(title_label)
        
        # 策略列表
        self.strategy_list = QListWidget()
        self.strategy_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.strategy_list)
        
        # 填充策略列表
        for strategy_name, strategy_class in self.strategies.items():
            item = QListWidgetItem(strategy_name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if strategy_name in self.selected_strategies else Qt.Unchecked)
            self.strategy_list.addItem(item)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 全选按钮
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_btn)
        
        # 取消全选按钮
        deselect_all_btn = QPushButton("取消全选")
        deselect_all_btn.clicked.connect(self.deselect_all)
        button_layout.addWidget(deselect_all_btn)
        
        # 保存模板按钮
        save_template_btn = QPushButton("保存模板")
        save_template_btn.clicked.connect(self.save_template)
        button_layout.addWidget(save_template_btn)
        
        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def load_strategies(self):
        """加载所有可用的策略"""
        try:
            # 获取strategy包的路径
            strategy_path = os.path.dirname(strategy.__file__)
            
            # 遍历strategy目录下的所有模块
            for _, name, _ in pkgutil.iter_modules([strategy_path]):
                if name != '__init__':
                    try:
                        # 动态导入模块
                        module = importlib.import_module(f'strategy.{name}')
                        
                        # 查找模块中的策略类
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if isinstance(attr, type) and 'Strategy' in attr_name:
                                self.strategies[attr_name] = attr
                                
                    except Exception as e:
                        self.logger.error(f"加载策略模块 {name} 失败: {str(e)}")
                        
            self.logger.info(f"成功加载 {len(self.strategies)} 个策略")
            
        except Exception as e:
            self.logger.error(f"加载策略失败: {str(e)}")
            
    def get_selected_strategies(self):
        """获取选中的策略"""
        selected = []
        for i in range(self.strategy_list.count()):
            item = self.strategy_list.item(i)
            if item.checkState() == Qt.Checked:
                strategy_name = item.text()
                if strategy_name in self.strategies:
                    selected.append({
                        'name': strategy_name,
                        'class': self.strategies[strategy_name]
                    })
        return selected
        
    def select_all(self):
        """全选"""
        for i in range(self.strategy_list.count()):
            self.strategy_list.item(i).setCheckState(Qt.Checked)
            
    def deselect_all(self):
        """取消全选"""
        for i in range(self.strategy_list.count()):
            self.strategy_list.item(i).setCheckState(Qt.Unchecked)
            
    def save_template(self):
        """保存策略选择模板"""
        try:
            selected = []
            for i in range(self.strategy_list.count()):
                item = self.strategy_list.item(i)
                if item.checkState() == Qt.Checked:
                    selected.append(item.text())
            
            template_file = os.path.join("config", "strategy_template.json")
            os.makedirs("config", exist_ok=True)
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(selected, f, ensure_ascii=False, indent=2)
                
            self.logger.info("策略模板保存成功")
            
        except Exception as e:
            self.logger.error(f"保存策略模板失败: {str(e)}")
            
    def load_strategy_template(self):
        """加载策略选择模板"""
        try:
            template_file = os.path.join("config", "strategy_template.json")
            if os.path.exists(template_file):
                with open(template_file, 'r', encoding='utf-8') as f:
                    self.selected_strategies = json.load(f)
                self.logger.info(f"加载策略模板成功: {len(self.selected_strategies)} 个策略")
            else:
                # 默认全选
                self.selected_strategies = list(self.strategies.keys())
                
        except Exception as e:
            self.logger.error(f"加载策略模板失败: {str(e)}")
            # 默认全选
            self.selected_strategies = list(self.strategies.keys())

def show_strategy_selector(parent=None, logger_manager=None):
    """显示策略选择对话框"""
    dialog = StrategySelector(parent, logger_manager)
    if dialog.exec_():
        return dialog.get_selected_strategies()
    return None 