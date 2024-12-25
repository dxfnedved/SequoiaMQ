import os
from openai import OpenAI
import json
from logger_manager import LoggerManager
from dotenv import load_dotenv
import traceback
import time
import re
import httpx

from typing import Optional, Dict, Any
from colorama import Fore, Style

class LLMInterface:
    """大模型接口类"""
    
    def __init__(self, logger_manager=None):
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("llm_interface")
        
        # 加载环境变量
        load_dotenv()
        
        # 初始化OpenAI客户端
        api_key = os.getenv('LLM_API_KEY')
        base_url = os.getenv('LLM_API_ENDPOINT', 'https://api.deepseek.com')
        
        if not api_key:
            raise ValueError("LLM_API_KEY environment variable is not set")
            
        # 配置客户端，确保正确处理UTF-8编码
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=httpx.Client(
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                transport=httpx.HTTPTransport(retries=3)
            )
        )
        
        self.conversation_history = []
        
    def analyze_with_cot(self, prompt: str, context: str) -> Optional[Dict[str, Any]]:
        """使用Chain of Thought方法进行分析"""
        try:
            # 使用英文系统提示，避免编码问题
            system_prompt = "You are a professional financial analyst. Please analyze the following information and provide a response in valid JSON format."
            
            # 构建消息，确保使用UTF-8编码
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"{context}\n\n{prompt}"
                }
            ]
            
            # 调用API进行分析
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    self.logger.info("正在调用DeepSeek API...")
                    response = self.client.chat.completions.create(
                        model="deepseek-chat",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    # 获取回复内容
                    result = response.choices[0].message.content
                    self.logger.info("收到API响应")
                    
                    # 尝试解析JSON结果
                    try:
                        # 清理JSON字符串
                        result = self._clean_json_string(result)
                        
                        # 解析JSON
                        analysis_result = self._parse_json_result(result)
                        if analysis_result:
                            return analysis_result
                            
                    except json.JSONDecodeError as e:
                        self.logger.error(f"JSON解析失败: {str(e)}")
                        retry_count += 1
                        if retry_count < max_retries:
                            self.logger.info(f"正在重试 ({retry_count}/{max_retries})...")
                            time.sleep(2)
                        continue
                        
                except Exception as e:
                    self.logger.error(f"调用API失败: {str(e)}")
                    retry_count += 1
                    if retry_count < max_retries:
                        self.logger.info(f"正在重试 ({retry_count}/{max_retries})...")
                        time.sleep(2)
                    else:
                        self.logger.error(traceback.format_exc())
                        return None
                        
            return None
                
        except Exception as e:
            self.logger.error(f"分析过程失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
            
    def _clean_json_string(self, text: str) -> str:
        """清理JSON字符串"""
        try:
            # 移除非打印字符
            text = ''.join(char for char in text if ord(char) >= 32)
            
            # 查找JSON内容
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = text[start_idx:end_idx]
                self.logger.debug(f"提取的JSON字符串: {json_str[:200]}...")
                return json_str
            else:
                self.logger.error("未找到有效的JSON内容")
                return text
                
        except Exception as e:
            self.logger.error(f"清理JSON字符串失败: {str(e)}")
            return text
            
    def _parse_json_result(self, json_str: str) -> Optional[Dict[str, Any]]:
        """解析JSON结果"""
        try:
            # 尝试直接解析
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试修复常见问题
                # 1. 处理未转义的引号
                json_str = json_str.replace('"', '\\"').replace('\'', '"')
                # 2. 处理末尾可能缺少的大括号
                if json_str.count('{') > json_str.count('}'):
                    json_str += '}'
                # 3. 处理多余的逗号
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                
                return json.loads(json_str)
                
        except Exception as e:
            self.logger.error(f"JSON解析失败: {str(e)}")
            self.logger.debug(f"问题JSON字符串: {json_str}")
            return None
            
    def analyze_news(self, prompt: str) -> Optional[Dict[str, Any]]:
        """分析新闻（保持向后兼容）"""
        try:
            return self.analyze_with_cot(prompt, "请分析以下财经新闻并提供投资建议。")
        except Exception as e:
            self.logger.error(f"新闻分析失败: {str(e)}")
            return None
            
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
            科技、医药、能源、消费、金融、地产、周期、农业、军工、传媒
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
            return None
            
    def clear_conversation_history(self):
        """清除对话历史"""
        self.conversation_history = []