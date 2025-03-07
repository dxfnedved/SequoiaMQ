from news_crawler import NewsCrawler
from technical_analyzer import TechnicalAnalyzer
from llm_interface import LLMInterface
from loguru import logger

class WorkflowManager:
    """工作流管理器"""
    
    def __init__(self):
        self.logger = logger.bind(name="workflow_manager")
        self.news_crawler = NewsCrawler()
        self.tech_analyzer = TechnicalAnalyzer()
        self.llm = LLMInterface()
        
    def analyze_stock(self, code_or_name: str) -> bool:
        """分析股票
        
        Args:
            code_or_name: 股票代码或名称
        Returns:
            bool: 分析是否成功
        """
        try:
            # 获取新闻数据
            news_df = self.news_crawler.get_aggregated_news(code_or_name)
            if news_df.empty:
                self.logger.error(f"未找到股票 {code_or_name} 的新闻数据")
                return False
                
            # 获取技术指标
            indicators = self.tech_analyzer.get_technical_indicators(code_or_name)
            if not indicators:
                self.logger.error(f"获取股票 {code_or_name} 的技术指标失败")
                return False
                
            # 打印技术指标
            self._print_technical_analysis(indicators)
            
            # 获取股票代码和名称
            stock_code = self.news_crawler._get_full_stock_code(code_or_name)
            stock_name = self.news_crawler._get_stock_name(stock_code)
            
            # 准备新闻列表
            news_list = [
                f"[{row['time'].strftime('%Y-%m-%d %H:%M')}] {row['title']}\n"
                f"来源: {row['source']}\n{row['content']}"
                for _, row in news_df.iterrows()
            ]
            
            # 使用大模型进行分析
            print("\n=== 正在进行AI分析 ===")
            analysis_result = self.llm.analyze_with_cot(
                stock_code=stock_code,
                stock_name=stock_name,
                news_list=news_list,
                technical_indicators=indicators
            )
            
            if not analysis_result:
                self.logger.error("AI分析失败")
                return False
                
            # 打印分析结果
            self._print_analysis_result(analysis_result)
            
            return True
            
        except Exception as e:
            self.logger.error(f"分析股票 {code_or_name} 时发生错误: {str(e)}")
            return False
            
    def _print_technical_analysis(self, indicators: dict):
        """打印技术分析结果"""
        if not indicators:
            logger.warning("没有可用的技术指标数据")
            return
        
        # MA 分析
        print("\n=== 技术指标分析 ===")
        ma_data = indicators.get('MA', {})
        if ma_data:
            print(f"MA5: {ma_data.get('MA5', 'N/A')}")
            print(f"MA10: {ma_data.get('MA10', 'N/A')}")
            print(f"MA20: {ma_data.get('MA20', 'N/A')}")
        
        # MACD 分析
        macd_data = indicators.get('MACD', {})
        if macd_data:
            print("\nMACD: {:.2f}".format(macd_data.get('MACD', 0)))
            print("Signal: {:.2f}".format(macd_data.get('Signal', 0)))
            print("Histogram: {:.2f}".format(macd_data.get('Histogram', 0)))
        
        # RSI 分析
        rsi_data = indicators.get('RSI', 0)
        if isinstance(rsi_data, dict):
            print("\nRSI: {:.2f}".format(rsi_data.get('RSI', 0)))
        else:
            print("\nRSI: {:.2f}".format(float(rsi_data)))
        
        # 布林带分析
        boll_data = indicators.get('BOLL', {})
        if boll_data:
            print("\n=== 布林带 ===")
            print(f"上轨: {boll_data.get('upper', 'N/A')}")
            print(f"中轨: {boll_data.get('middle', 'N/A')}")
            print(f"下轨: {boll_data.get('lower', 'N/A')}")
        
        # 价格信息
        price_data = indicators.get('PRICE', {})
        if price_data:
            print("\n=== 价格信息 ===")
            print(f"开盘: {price_data.get('Open', 'N/A')}")
            print(f"最高: {price_data.get('High', 'N/A')}")
            print(f"最低: {price_data.get('Low', 'N/A')}")
            print(f"收盘: {price_data.get('Close', 'N/A')}")
            print(f"涨跌幅: {price_data.get('Change', 'N/A')}%")
        
        # 成交量分析
        volume_data = indicators.get('VOLUME', {})
        if volume_data:
            print("\n=== 成交量分析 ===")
            print(f"成交量: {volume_data.get('Volume', 'N/A')}")
            print(f"成交额: {volume_data.get('Amount', 'N/A')}")
            print(f"换手率: {volume_data.get('Turnover', 'N/A')}%")
            print(f"5日均量: {volume_data.get('VolumeMA5', 'N/A')}")
            print(f"10日均量: {volume_data.get('VolumeMA10', 'N/A')}")
        
    def _print_analysis_result(self, result: dict):
        """打印分析结果
        
        Args:
            result: AI分析结果字典
        """
        print("\n=== AI分析结果 ===")
        print(f"情感评分: {result.get('sentiment_score', 0.0)}")
        print(f"新闻影响范围: {result.get('news_spread', 1)}")
        print(f"市场影响: {result.get('market_impact', '中性')}\n")
        
        print("主要利好因素:")
        for factor in result.get('positive_factors', ['数据不足']):
            print(f"- {factor}")
        print()
        
        print("主要风险因素:")
        for factor in result.get('risk_factors', ['数据不足']):
            print(f"- {factor}")
        print()
        
        print("-----价格预测-----:")
        price_prediction = result.get('price_prediction', {})
        if isinstance(price_prediction, dict):
            min_price = price_prediction.get('min')
            max_price = price_prediction.get('max')
            print(f"价格预测: 预计在 {min_price} - {max_price} 区间波动")
        else:
            print(f"价格预测: {price_prediction}")
            
        print(f"投资建议: {result.get('recommendation', '建议观望')}\n")
        print(f"分析总结: {result.get('analysis_summary', '无分析总结')}") 