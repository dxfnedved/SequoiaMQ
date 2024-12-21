import os
from openai import OpenAI
import json
from logger_manager import LoggerManager
from dotenv import load_dotenv
import traceback

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
            
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        self.conversation_history = []
        
    def analyze_with_cot(self, prompt: str, context: str) -> Optional[Dict[str, Any]]:
        """使用Chain of Thought方法进行分析"""
        try:
            # 添加思维链提示
            cot_prompt = f"""
            {context}
            
            请按照以下步骤进行分析：
            1. 仔细阅读并理解所提供的信息
            2. 列出关键信息点和重要发现
            3. 分析这些信息之间的关联性
            4. 推理可能的影响和结果
            5. 得出结论并提供建议
            
            请一步步思考并说明推理过程。
            
            {prompt}
            """
            
            # 将当前对话添加到历史记录
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的金融分析师，擅长通过逐步推理来分析市场信息。请确保返回的结果是有效的JSON格式。"
                }
            ]
            
            # 添加历史对话
            messages.extend(self.conversation_history)
            
            # 添加当前提示
            messages.append({
                "role": "user",
                "content": cot_prompt
            })
            
            # 调用API进行分析
            try:
                self.logger.info("正在调用DeepSeek API...")
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000,
                    stream=False
                )
                
                # 获取回复内容
                result = response.choices[0].message.content
                self.logger.info("收到API响应")
                
                # 将助手的回复添加到历史记录
                self.conversation_history.append({
                    "role": "assistant",
                    "content": result
                })
                
                # 尝试解析JSON结果
                try:
                    # 确保结果是UTF-8编码
                    if isinstance(result, str):
                        result = result.encode('utf-8', errors='ignore').decode('utf-8')
                        self.logger.debug(f"UTF-8编码后的结果长度: {len(result)}")
                    
                    # 清理JSON字符串中的特殊字符
                    result = ''.join(char for char in result if ord(char) >= 32)
                    
                    # 查找JSON内容（防止模型返回额外的解释文本）
                    start_idx = result.find('{')
                    end_idx = result.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = result[start_idx:end_idx]
                        self.logger.debug(f"提取的JSON字符串: {json_str[:200]}...")
                        
                        # 解析JSON
                        analysis_result = json.loads(json_str)
                        return analysis_result
                    else:
                        self.logger.error("响应中未找到有效的JSON内容")
                        self.logger.debug(f"原始响应: {result[:500]}...")
                        return None
                        
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON解析失败: {str(e)}")
                    self.logger.error(f"原始结果: {result[:500]}...")  # 只记录前500个字符
                    return None
                    
            except Exception as e:
                self.logger.error(f"调用API失败: {str(e)}")
                self.logger.error(traceback.format_exc())
                return None
                
        except Exception as e:
            self.logger.error(f"分析过程失败: {str(e)}")
            self.logger.error(traceback.format_exc())
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
            科技、医药、新能源、消费、金融、地产、周期��农业、军工、传媒
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