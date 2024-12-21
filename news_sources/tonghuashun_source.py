from .base_source import NewsSource
from datetime import datetime
import time
import random
from typing import List, Dict
import pywencai

class TonghuashunSource(NewsSource):
    """同花顺新闻源"""
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.name = "同花顺"
        
    def fetch_news(self, limit: int = 100) -> List[Dict]:
        """获取同花顺新闻"""
        try:
            # 使用问财获取新闻
            question = "最新的财经新闻"
            w = pywencai.get(question=question)
            
            if w is None or w.empty:
                if self.logger:
                    self.logger.warning("未获取到同花顺新闻")
                return []
                
            news_list = []
            for _, row in w.iterrows():
                try:
                    # 提取新闻信息
                    title = str(row.get('title', ''))
                    content = str(row.get('content', ''))
                    news_time = row.get('time', datetime.now())
                    url = str(row.get('url', ''))
                    
                    if not title or not content:
                        continue
                        
                    news_list.append({
                        'title': title,
                        'content': content,
                        'time': news_time,
                        'url': url,
                        'source': self.name
                    })
                    
                    if len(news_list) >= limit:
                        break
                        
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"处理同花顺新闻项时出错: {str(e)}")
                    continue
                    
            return news_list
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"获取同花顺新闻失败: {str(e)}")
            return [] 