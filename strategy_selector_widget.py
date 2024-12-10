from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QCheckBox, QPushButton,
    QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, Signal
import json
from logger_manager import LoggerManager

class StrategySelector(QWidget):
    """策略选择组件"""
    strategies_changed = Signal(list)  # 选中的策略列表

    def __init__(self, parent=None, logger_manager=None):
        super().__init__(parent)
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("strategy_selector")
        
        # 策略列表
        self.strategies = {
            'RSRS': {
                'name': 'RSRS策略',
                'description': '阻力支撑相对强度策略'
            },
            'Alpha101': {
                'name': 'Alpha101策略',
                'description': '基于Alpha101因子的选股策略'
            },
            'Alpha191': {
                'name': 'Alpha191策略',
                'description': '基于Alpha191因子的选股策略'
            },
            'TurtleStrategy': {
                'name': '海龟交易策略',
                'description': '基于趋势跟踪的海龟交易法则'
            },
            'EnterStrategy': {
                'name': '入场策略',
                'description': '基于突破和成交量的入场策略'
            },
            'LowATRStrategy': {
                'name': '低波动策略',
                'description': '基于ATR指标的低波动选股策略'
            },
            'LowBacktraceIncreaseStrategy': {
                'name': '低回撤增长策略',
                'description': '寻找低回撤且稳定增长的股票'
            },
            'KeepIncreasingStrategy': {
                'name': '持续上涨策略',
                'description': '寻找持续上涨趋势的股票'
            },
            'BacktraceMA250Strategy': {
                'name': '回踩年线策略',
                'description': '寻找回踩年线支撑的股票'
            }
        }
        
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 创建内容容器
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # 策略选择组
        strategy_group = QGroupBox("选择策略")
        strategy_layout = QVBoxLayout()
        
        # 添加策略复选框
        self.checkboxes = {}
        for key, info in self.strategies.items():
            checkbox = QCheckBox(f"{info['name']} - {info['description']}")
            checkbox.stateChanged.connect(self.on_strategy_changed)
            self.checkboxes[key] = checkbox
            strategy_layout.addWidget(checkbox)
            
        strategy_group.setLayout(strategy_layout)
        content_layout.addWidget(strategy_group)
        
        # 按钮
        btn_layout = QVBoxLayout()
        
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self.select_all)
        btn_layout.addWidget(select_all_btn)
        
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self.clear_all)
        btn_layout.addWidget(clear_btn)
        
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)
        
        content_layout.addLayout(btn_layout)
        content_layout.addStretch()
        
        # 设置滚动区域的内容
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
    def on_strategy_changed(self):
        """处理策略选择变化"""
        try:
            selected = []
            for key, checkbox in self.checkboxes.items():
                if checkbox.isChecked():
                    selected.append(key)
            self.strategies_changed.emit(selected)
            self.logger.info(f"选中的策略: {selected}")
        except Exception as e:
            self.logger.error(f"处理策略选择变化失败: {str(e)}")
            
    def select_all(self):
        """全选"""
        try:
            for checkbox in self.checkboxes.values():
                checkbox.setChecked(True)
        except Exception as e:
            self.logger.error(f"全选失败: {str(e)}")
            
    def clear_all(self):
        """清空"""
        try:
            for checkbox in self.checkboxes.values():
                checkbox.setChecked(False)
        except Exception as e:
            self.logger.error(f"清空失败: {str(e)}")
            
    def save_settings(self):
        """保存设置"""
        try:
            settings = {
                key: checkbox.isChecked()
                for key, checkbox in self.checkboxes.items()
            }
            
            with open('data/strategy_settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
                
            QMessageBox.information(self, "成功", "策略设置已保存")
            self.logger.info("保存策略设置成功")
            
        except Exception as e:
            self.logger.error(f"保存策略设置失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"保存设置失败: {str(e)}")
            
    def load_settings(self):
        """加载设置"""
        try:
            try:
                with open('data/strategy_settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                for key, checked in settings.items():
                    if key in self.checkboxes:
                        self.checkboxes[key].setChecked(checked)
                        
                self.logger.info("加载策略设置成功")
                
            except FileNotFoundError:
                # 默认选中RSRS和Alpha101策略
                self.checkboxes['RSRS'].setChecked(True)
                self.checkboxes['Alpha101'].setChecked(True)
                self.logger.info("使用默认策略设置")
                
        except Exception as e:
            self.logger.error(f"加载策略设置失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"加载设置失败: {str(e)}")
            
    def get_selected_strategies(self):
        """获取选中的策略"""
        return [
            key for key, checkbox in self.checkboxes.items()
            if checkbox.isChecked()
        ] 