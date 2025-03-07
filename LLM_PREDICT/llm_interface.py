import os
from openai import OpenAI
import json
from loguru import logger
from dotenv import load_dotenv
import traceback
import re
import tiktoken

class LLMInterface:
    """大模型接口类"""
    
    def __init__(self):
        self.logger = logger.bind(name="llm_interface")
        self.max_tokens = 65536

        try:
            # 加载环境变量
            load_dotenv(verbose=True)  # 添加 verbose=True 来显示加载过程
            
            # 获取并验证 API 密钥
            self.api_key = os.getenv('LLM_API_KEY')
            self.base_url = os.getenv('LLM_API_ENDPOINT', 'https://api.deepseek.com/v1')
            self.model_name = os.getenv('LLM_MODEL_NAME', 'deepseek-chat')
            
            # 打印环境变量加载情况（不要在生产环境中显示完整的 API 密钥）
            print("\n=== 环境变量加载情况 ===")
            print(f"API 端点: {self.base_url}")
            print(f"API 密钥: {'已设置' if self.api_key else '未设置'}")
            if self.api_key:
                print(f"API 密钥前10位: {self.api_key[:10]}...")
            
            if not self.api_key:
                raise ValueError("LLM_API_KEY environment variable is not set")
            
            # 使用类属性而不是局部变量
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            self.conversation_history = []
            
        except Exception as e:
            print(f"\n初始化失败: {str(e)}")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误详情: {traceback.format_exc()}")
            print("\n请检查以下内容：")
            print("1. .env 文件是否存在于正确的目录")
            print("2. .env 文件中是否包含 LLM_API_KEY")
            print("3. .env 文件的格式是否正确")
            print("\n当前工作目录:", os.getcwd())
            print("\n.env 文件内容:")
            try:
                if os.path.exists('.env'):
                    with open('.env', 'r', encoding='utf-8') as f:
                        print(f.read())
                else:
                    print(".env 文件不存在")
            except Exception as e:
                print(f"读取 .env 文件失败: {str(e)}")
            raise
        
    def _count_tokens(self, text: str) -> int:
        """计算文本的token数量
        
        使用字符分类方法估算token数量:
        - 中文字符: 1.5个token
        - 英文单词: 0.8个token
        - 数字: 0.5个token
        - 标点符号: 0.3个token
        - 空白字符: 0.2个token
        
        Args:
            text: 需要计算的文本
            
        Returns:
            int: 估算的token数量
        """
        try:
            if not text:
                return 0
                
            # 使用正则表达式匹配不同类型的字符
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))  # 中文字符
            english_words = len(re.findall(r'[a-zA-Z]+', text))  # 英文单词
            numbers = len(re.findall(r'\d+', text))  # 数字
            punctuation = len(re.findall(r'[^\w\s\u4e00-\u9fff]', text))  # 标点符号
            whitespace = len(re.findall(r'\s+', text))  # 空白字符
            
            # 计算估算的token数量
            estimated_tokens = (
                chinese_chars * 1.5 +  # 中文字符权重
                english_words * 0.8 +  # 英文单词权重
                numbers * 0.5 +  # 数字权重
                punctuation * 0.3 +  # 标点符号权重
                whitespace * 0.2  # 空白字符权重
            )
            
            # 向上取整
            token_count = int(estimated_tokens + 0.5)
            
            # 记录详细的token计算信息
            self.logger.debug(
                f"Token估算明细:\n"
                f"- 中文字符: {chinese_chars} * 1.5 = {chinese_chars * 1.5}\n"
                f"- 英文单词: {english_words} * 0.8 = {english_words * 0.8}\n"
                f"- 数字: {numbers} * 0.5 = {numbers * 0.5}\n"
                f"- 标点符号: {punctuation} * 0.3 = {punctuation * 0.3}\n"
                f"- 空白字符: {whitespace} * 0.2 = {whitespace * 0.2}\n"
                f"总计: {token_count} tokens"
            )
            
            return token_count
            
        except Exception as e:
            self.logger.error(f"Token计算失败: {str(e)}")
            # 发生错误时返回保守估计
            return len(text)
            
    def analyze_with_cot(self, stock_code: str, stock_name: str, news_list: list, technical_indicators: dict) -> dict:
        """使用思维链进行分析"""
        try:
            # 构建系统提示
            system_prompt = """
            你是一个专业的金融分析师，擅长通过新闻情感分析来预测股票走势。
            请基于新闻传播广度、市场情绪和技术面进行综合分析。
            重点关注新闻的传播范围和影响力，这些因素会显著影响短期股价走势。
            请确保返回的 JSON 格式正确，不要包含任何注释。
            """
            
            # 构建用户提示
            user_prompt = f"""
            请按照以下步骤分析股票 {stock_code} ({stock_name}):

            1. 新闻情感分析
               - 仔细阅读每条新闻内容
               - 评估新闻的情感倾向（正面/负面/中性）
               - 分析新闻的传播范围和影响力
               - 总结新闻反映的主要利好和风险因素

            2. 技术指标分析
               - 分析价格趋势和成交量变化
               - 评估MA、RSI、MACD等技术指标
               - 识别可能的支撑位和压力位
               - 判断技术面的整体走势

            最新新闻:
            {chr(10).join(news_list)}

            技术指标:
            {json.dumps(technical_indicators, ensure_ascii=False, indent=2)}

            请返回一个格式正确的 JSON 对象，包含以下字段：
            - sentiment_score: 情感评分，范围从 -1 到 1
            - news_spread: 新闻影响范围，范围从 1 到 5
            - market_impact: 市场影响，可选值：利好、利空、中性
            - positive_factors: 主要利好因素列表
            - risk_factors: 主要风险因素列表
            - price_prediction: 价格预测，包含具体区间，使用min, max表示价格最低值和最高值
            - recommendation: 投资建议，可选值：买入、持有、卖出
            - analysis_summary: 分析总结

            注意：请确保返回的是一个有效的 JSON 对象，不要包含任何注释或说明文字。相同的利好、利空消息进行去重。
            """
            
            # 计算 token 使用量
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            total_tokens = sum(self._count_tokens(msg["content"]) for msg in messages)
            self.logger.info(f"预计 token 使用量: {total_tokens}")
            
            # 如果超出限制,尝试缩减内容
            if total_tokens > self.max_tokens * 0.9:  # 留出 10% 的余量给响应
                self.logger.warning("Token 使用量超出限制,尝试缩减内容...")
                # 缩减新闻列表长度
                while total_tokens > self.max_tokens * 0.9 and len(news_list) > 5:
                    news_list = news_list[:len(news_list)-1]  # 移除最后一条新闻
                    user_prompt = f"""
            请按照以下步骤分析股票 {stock_code} ({stock_name}):

            1. 新闻情感分析
               - 仔细阅读每条新闻内容
               - 评估新闻的情感倾向（正面/负面/中性）
               - 分析新闻的传播范围和影响力
               - 总结新闻反映的主要利好和风险因素

            2. 技术指标分析
               - 分析价格趋势和成交量变化
               - 评估MA、RSI、MACD等技术指标
               - 识别可能的支撑位和压力位
               - 判断技术面的整体走势

            最新新闻:
            {chr(10).join(news_list)}

            技术指标:
            {json.dumps(technical_indicators, ensure_ascii=False, indent=2)}

            请返回一个格式正确的 JSON 对象，包含以下字段：
            - sentiment_score: 情感评分，范围从 -1 到 1
            - news_spread: 新闻影响范围，范围从 1 到 5
            - market_impact: 市场影响，可选值：利好、利空、中性
            - positive_factors: 主要利好因素列表
            - risk_factors: 主要风险因素列表
            - price_prediction: 价格预测，包含具体区间，使用min, max表示价格最低值和最高值
            - recommendation: 投资建议，可选值：买入、持有、卖出
            - analysis_summary: 分析总结

            注意：请确保返回的是一个有效的 JSON 对象，不要包含任何注释或说明文字。相同的利好、利空消息进行去重。
            """
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                    total_tokens = sum(self._count_tokens(msg["content"]) for msg in messages)
                    self.logger.debug(f"发送给大模型的消息: {messages}")
                
            try:
                # 调用 API
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=min(8192, self.max_tokens - total_tokens),  # 动态调整响应长度
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stream=False,
                    # request_timeout=self.timeout  # 使用request_timeout而不是timeout
                )
                self.logger.debug(f"发送给大模型的消息: {messages}")
                
                # 记录实际 token 使用情况
                if hasattr(response, 'usage'):
                    self.logger.info(f"实际 token 使用量: {response.usage}")
                
                result = response.choices[0].message.content
                return self._clean_json_string(result)
                
            except Exception as e:
                self.logger.error(f"API调用失败: {str(e)}")
                return self._get_default_analysis()
            
        except Exception as e:
            self.logger.error(f"分析过程出错: {str(e)}")
            return self._get_default_analysis()
            
    def _clean_json_string(self, text: str) -> dict:
        """清理JSON字符串"""
        try:
            # 移除非打印字符
            text = ''.join(char for char in text if ord(char) >= 32)
            
            # 查找JSON内容（在```json和```之间）
            json_pattern = r'```json\s*(.*?)\s*```'
            match = re.search(json_pattern, text, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
            else:
                # 如果没有找到```json标记，尝试直接查找JSON对象
                start_idx = text.find('{')
                end_idx = text.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = text[start_idx:end_idx].strip()
                else:
                    self.logger.error("未找到有效的JSON内容")
                    return self._get_default_analysis()
            
            # 尝试解析JSON
            try:
                parsed_json = json.loads(json_str)
                
                # 确保所有必要的字段都存在
                required_fields = [
                    'sentiment_score', 'news_spread', 'market_impact',
                    'positive_factors', 'risk_factors', 'price_prediction',
                    'recommendation', 'analysis_summary'
                ]
                
                # 如果缺少任何必要字段，返回默认分析结果
                if not all(field in parsed_json for field in required_fields):
                    self.logger.error("缺少必要字段")
                    return self._get_default_analysis()
                
                return parsed_json
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败: {str(e)}")
                self.logger.debug(f"清理后的JSON字符串: {json_str}")
                return self._get_default_analysis()
            
        except Exception as e:
            self.logger.error(f"清理JSON字符串失败: {str(e)}")
            return self._get_default_analysis()
            
    # def _parse_json_result(self, json_str: str) -> dict:
    #     """解析JSON结果"""
    #     try:
    #         # 如果输入为空，返回默认分析结果
    #         if not json_str:
    #             self.logger.error("JSON字符串为空")
    #             return self._get_default_analysis()
            
    #         # 如果输入已经是字典，直接使用
    #         if isinstance(json_str, dict):
    #             result = json_str
    #         else:
    #             # 尝试清理和解析JSON
    #             result = self._clean_json_string(json_str)
            
    #         # 如果结果为空字典，返回默认分析结果
    #         if not result:
    #             return self._get_default_analysis()
            
    #         # 验证必要字段
    #         required_fields = [
    #             'sentiment_score', 'news_spread', 'market_impact',
    #             'positive_factors', 'risk_factors', 'price_prediction',
    #             'recommendation', 'analysis_summary'
    #         ]
            
    #         missing_fields = [field for field in required_fields if field not in result]
    #         if missing_fields:
    #             self.logger.error(f"缺少必要字段: {', '.join(missing_fields)}")
    #             return self._get_default_analysis()
                
    #         return result
            
    #     except Exception as e:
    #         self.logger.error(f"JSON解析失败: {str(e)}")
    #         self.logger.debug(f"问题JSON字符串: {json_str}")
    #         return self._get_default_analysis()
            
    def analyze_news(self, prompt: str) -> dict:
        """分析新闻（保持向后兼容）"""
        try:
            return self.analyze_with_cot(prompt, "请分析以下财经新闻并提供投资建议。")
        except Exception as e:
            self.logger.error(f"新闻分析失败: {str(e)}")
            return {}
            
    def get_stock_industry(self, stock_info):
        """获取股票所属行业"""
        try:
            # 确保输入是UTF-8编码
            code = str(stock_info.get('code', '')).encode('utf-8', errors='ignore').decode('utf-8')
            name = str(stock_info.get('name', '')).encode('utf-8', errors='ignore').decode('utf-8')
            
            prompt = f"""
            请分析以下股票信息，判断其所属行业：
            
            股票代码：{code}
            股票名称：{name}
            
            请直接返回行业名称，不需要其他解释。行业分类应该是以下之一：
            科技、医药、新能源、消费、金融、地产、周期、农业、军工、传媒
            """
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的股票分析师，擅长股票分类。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50,
                stream=False
            )
            
            # 确保响应内容是UTF-8编码
            industry = response.choices[0].message.content.strip()
            if isinstance(industry, str):
                industry = industry.encode('utf-8', errors='ignore').decode('utf-8')
            
            return industry
            
        except Exception as e:
            self.logger.error(f"获取股票行业失败: {str(e)}")
            return {}
            
    def clear_conversation_history(self):
        """清除对话历史"""
        self.conversation_history = []

    def _get_default_analysis(self) -> dict:
        """获取默认的分析结果"""
        return {
            'sentiment_score': 0.0,
            'news_spread': 1,
            'market_impact': '中性',
            'positive_factors': ['数据不足'],
            'risk_factors': ['数据不足'],
            'price_prediction': '数据不足，无法预测',
            'recommendation': '建议观望',
            'analysis_summary': '无分析总结'
        }