def analyze_stock(self):
    """分析当前选中的股票"""
    try:
        if not hasattr(self, 'current_code') or not self.current_code:
            self.logger.warning("请先选择股票")
            return
            
        # 获取分析结果
        results = self.work_flow.analyze_stock(self.current_code)
        
        # 显示分析结果对话框
        from analysis_dialog import show_analysis_dialog
        show_analysis_dialog(
            self.current_code,
            self.current_name,
            results,
            self,
            self.logger_manager
        )
        
    except Exception as e:
        self.logger.error(f"分析股票失败: {str(e)}")

def on_stock_selected(self, code, name):
    """处理股票选择"""
    try:
        self.current_code = code
        self.current_name = name
        self.logger.info(f"选择股票: {code} - {name}")
        
        # 更新图表
        self.stock_chart.update_chart(code, name)
        
    except Exception as e:
        self.logger.error(f"处理股票选择失败: {str(e)}")

def init_ui(self):
    """初��化UI"""
    # ... 其他UI初始化代码 ...
    
    # 分析按钮
    analyze_btn = QPushButton("分析")
    analyze_btn.clicked.connect(self.analyze_stock)
    toolbar_layout.addWidget(analyze_btn)
    
    # ... 其他UI初始化代码 ... 