"""Analysis result dialog implementation."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QFileDialog
)
from PySide6.QtCore import Qt
import pandas as pd
import json
from logger_manager import LoggerManager

def show_analysis_dialog(code, name, results, parent=None, logger_manager=None):
    """显示分析结果对话框"""
    dialog = AnalysisDialog(code, name, results, parent, logger_manager)
    dialog.exec_()

class AnalysisDialog(QDialog):
    """分析结果对话框"""
    def __init__(self, code, name, results, parent=None, logger_manager=None):
        super().__init__(parent)
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("analysis_dialog")
        
        self.code = code
        self.name = name
        self.results = results
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"分析结果 - {self.name}({self.code})")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # 结果显示
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.format_results()
        layout.addWidget(self.result_text)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存结果")
        save_btn.clicked.connect(self.save_results)
        button_layout.addWidget(save_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def format_results(self):
        """格式化分析结果"""
        try:
            if not self.results:
                self.result_text.setText("没有分析结果")
                return
                
            text = f"分析时间: {self.results.get('timestamp', '')}\n\n"
            
            # 策略结果
            for strategy, result in self.results.items():
                if strategy != 'timestamp':
                    text += f"=== {strategy} ===\n"
                    for key, value in result.items():
                        text += f"{key}: {value}\n"
                    text += "\n"
                    
            self.result_text.setText(text)
            
        except Exception as e:
            self.logger.error(f"格式化分析结果失败: {str(e)}")
            self.result_text.setText("格式化结果失败")
            
    def save_results(self):
        """保存分析结果"""
        try:
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存分析结果",
                f"analysis_{self.code}_{self.name}.json",
                "JSON文件 (*.json)"
            )
            
            if not file_path:
                return
                
            # 保存结果
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"保存分析结果到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存分析结果失败: {str(e)}") 