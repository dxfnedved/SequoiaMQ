from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTextEdit, QFileDialog)
from PySide6.QtCore import Qt
import pandas as pd
import json
from logger_manager import LoggerManager

class AnalysisDialog(QDialog):
    """分析结果对话框"""
    def __init__(self, code, name, results, parent=None, logger_manager=None):
        super().__init__(parent)
        # 初始化日志管理器
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("analysis_dialog")
        
        self.code = code
        self.name = name
        self.results = results
        
        self.init_ui()
        self.display_results()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"分析结果 - {self.code} {self.name}")
        self.setModal(True)
        self.resize(800, 600)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(f"股票: {self.code} - {self.name}")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(title_label)
        
        # 结果显示区域
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 导出按钮
        export_btn = QPushButton("导出JSON")
        export_btn.clicked.connect(self.export_results)
        button_layout.addWidget(export_btn)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def display_results(self):
        """显示分析结果"""
        try:
            if not self.results:
                self.result_text.setText("没有分析结果")
                return
            
            # 格式化显示结果
            if isinstance(self.results, dict):
                if len(self.results) == 1:
                    # 单个股票的结果
                    text = []
                    for key, value in self.results.items():
                        if isinstance(value, (int, float)):
                            value = round(value, 4)
                        text.append(f"{key}: {value}")
                else:
                    # 批量分析结果
                    text = []
                    for stock_name, stock_results in self.results.items():
                        text.append(f"\n{stock_name}:")
                        for key, value in stock_results.items():
                            if isinstance(value, (int, float)):
                                value = round(value, 4)
                            text.append(f"  {key}: {value}")
            
            self.result_text.setText("\n".join(text))
            
        except Exception as e:
            self.logger.error(f"显示分析结果失败: {str(e)}")
            self.result_text.setText("显示结果时出错")
            
    def export_results(self):
        """导出分析结果"""
        try:
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "导出分析结果",
                f"{self.code}_{self.name}_analysis.json" if len(self.results) == 1 else "batch_analysis.json",
                "JSON Files (*.json)"
            )
            
            if file_name:
                export_analysis_results(self.results, file_name)
                self.logger.info(f"分析结果已导出到: {file_name}")
                
        except Exception as e:
            self.logger.error(f"导出分析结果失败: {str(e)}")

def show_analysis_dialog(code, name, results, parent=None, logger_manager=None):
    """显示分析结果对话框的便捷函数"""
    dialog = AnalysisDialog(code, name, results, parent, logger_manager)
    dialog.exec_()
    
def export_analysis_results(results, file_name):
    """导出分析结果到JSON文件"""
    try:
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise Exception(f"导出分析结果失败: {str(e)}") 