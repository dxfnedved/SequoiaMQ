from strategy.base import BaseStrategy
from news_crawler import NewsCrawler
from llm_interface import LLMInterface
import os
import json
import time
from settings import NEWS_CACHE_DIR

class NewsStrategy(BaseStrategy):
    """新闻分析策略 - 市场整体分析"""
    
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "NewsStrategy"
        self.news_crawler = NewsCrawler(logger_manager)
        self.llm_interface = LLMInterface(logger_manager)
        self.cache_dir = NEWS_CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_file = os.path.join(self.cache_dir, 'news_analysis.json')
        self.news_data = None
        self.analysis_result = None
        
        # 重点关注的行业
        self.focus_industries = [
            "新质生产力",
            "半导体",
            "消费电子",
            "人工智能",
            "券商"
        ]
        
    def _get_llm_prompt(self, news_data):
        """生成大模型分析提示词"""
        prompt = """
        作为一个专业的金融分析师，请分析以下财经新闻，重点关注以下行业：
        - 新质生产力
        - 半导体
        - 消费电子
        - 人工智能
        - 券商

        新闻内容如下：
        {news_content}

        请提供以下格式的分析结果：
        1. A股市场整体趋势分析
        2. 重点行业分析（仅针对上述行业）
        3. 市场风险提示
        4. 投资建议

        请以JSON格式输出，包含以下字段：
        {{
            "market_trend": {{
                "direction": "上涨/震荡/下跌",
                "analysis": "市场趋势分析",
                "confidence": "高/中/低"
            }},
            "industry_analysis": [
                {{
                    "industry": "行业名称",
                    "trend": "上涨/震荡/下跌",
                    "analysis": "行业分析",
                    "hot_topics": ["热点1", "热点2"]
                }}
            ],
            "risk_warnings": ["风险1", "风险2"],
            "investment_advice": {{
                "short_term": "短期投资建议",
                "mid_term": "中期投资建议",
                "focus_sectors": ["重点关注行业1", "重点关注行业2"]
            }}
        }}
        """
        
        # 准备新闻内容
        news_content = "\n\n".join([
            f"标题：{row['title']}\n"
            f"时间：{row['time']}\n"
            f"内容：{row['content']}\n"
            for _, row in news_data.iterrows()
        ])
        
        return prompt.format(news_content=news_content)
        
    def _analyze_with_llm(self, prompt):
        """使用大模型进行分析"""
        try:
            result = self.llm_interface.analyze_news(prompt)
            if not result:
                return self._get_default_analysis()
                
            # 验证返回的JSON格式
            required_fields = ['market_trend', 'industry_analysis', 'risk_warnings', 'investment_advice']
            if not all(field in result for field in required_fields):
                self.logger.warning("LLM返回的分析结果缺少必要字段，使用默认分析")
                return self._get_default_analysis()
                
            return result
            
        except Exception as e:
            self.logger.error(f"大模型分析失败: {str(e)}")
            return self._get_default_analysis()
            
    def _get_default_analysis(self):
        """获取默认的分析结果"""
        return {
            "market_trend": {
                "direction": "震荡",
                "analysis": "市场整体呈现震荡态势，建议谨慎操作",
                "confidence": "中"
            },
            "industry_analysis": [
                {
                    "industry": industry,
                    "trend": "震荡",
                    "analysis": f"{industry}行业维持震荡走势，需要关注政策和行业基本面变化",
                    "hot_topics": ["政策支持", "技术创新"]
                }
                for industry in self.focus_industries
            ],
            "risk_warnings": [
                "市场波动风险",
                "政策调整风险",
                "行业周期风险"
            ],
            "investment_advice": {
                "short_term": "建议以观望为主，等待明确信号",
                "mid_term": "关注行业龙头，把握结构性机会",
                "focus_sectors": self.focus_industries[:3]
            }
        }
            
    def perform_global_analysis(self):
        """执行全局新闻分析"""
        try:
            # 检查缓存
            if os.path.exists(self.cache_file):
                cache_time = os.path.getmtime(self.cache_file)
                if time.time() - cache_time < 7200:  # 2小时内的缓存有效
                    try:
                        with open(self.cache_file, 'r', encoding='utf-8') as f:
                            self.analysis_result = json.load(f)
                            return True
                    except json.JSONDecodeError:
                        self.logger.warning("缓存文件损坏，将重新分析")
            
            # 获取新闻数据
            self.news_data = self.news_crawler.get_all_news()
            if self.news_data.empty:
                self.logger.warning("未获取到新闻数据，使用默认分析结果")
                self.analysis_result = self._get_default_analysis()
                return True
                
            # 生成提示词
            prompt = self._get_llm_prompt(self.news_data)
            
            # 使用大模型分析
            self.analysis_result = self._analyze_with_llm(prompt)
            if not self.analysis_result:
                self.logger.warning("新闻分析失败，使用默认分析结果")
                self.analysis_result = self._get_default_analysis()
                
            # 保存缓存
            try:
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self.analysis_result, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self.logger.error(f"保存新闻分析缓存失败: {str(e)}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"执行全局新闻分析失败: {str(e)}")
            self.analysis_result = self._get_default_analysis()
            return True  # 返回True以继续执行其他策略
            
    def analyze(self, data):
        """分析单个股票"""
        try:
            if not self.analysis_result:
                self.logger.warning("没有全局新闻分析结果，使用默认分析")
                self.analysis_result = self._get_default_analysis()
                
            # 获取股票所属行业
            industry = self._get_stock_industry(data)
            if not industry:
                return None
                
            # 只对重点关注的行业生成信号
            if industry not in self.focus_industries:
                return None
                
            # 查找行业分析
            industry_info = None
            for ind_analysis in self.analysis_result['industry_analysis']:
                if ind_analysis['industry'] == industry:
                    industry_info = ind_analysis
                    break
                    
            if not industry_info:
                return None
                
            # 根据行业趋势生成信号
            signal = self._generate_signal(industry_info)
            
            return {
                'signal': signal['action'],
                'factors': {
                    'industry': industry,
                    'trend': industry_info['trend'],
                    'analysis': industry_info['analysis'],
                    'market_trend': self.analysis_result['market_trend']['direction'],
                    'confidence': self.analysis_result['market_trend']['confidence']
                }
            }
            
        except Exception as e:
            self.logger.error(f"新闻策略分析失败: {str(e)}")
            return None
            
    def _get_stock_industry(self, data):
        """获取股票所属行业"""
        try:
            stock_info = {
                'code': data.name if hasattr(data, 'name') else None,
                'name': self.stock_names.get(data.name) if hasattr(data, 'name') else None
            }
            
            if not stock_info['code'] or not stock_info['name']:
                return None
                
            try:
                return self.llm_interface.get_stock_industry(stock_info)
            except Exception as e:
                self.logger.error(f"获取股票行业失败: {str(e)}")
                return None
                
        except Exception as e:
            self.logger.error(f"获取股票行业失败: {str(e)}")
            return None
            
    def _generate_signal(self, industry_info):
        """根据行业分析生成信号"""
        try:
            trend = industry_info['trend']
            
            if trend == '上涨':
                return {'action': '买入'}
            elif trend == '下跌':
                return {'action': '卖出'}
            else:
                return {'action': '观望'}
                
        except Exception as e:
            self.logger.error(f"生成信号失败: {str(e)}")
            return {'action': '观望'}
