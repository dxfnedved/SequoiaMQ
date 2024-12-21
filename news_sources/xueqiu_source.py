from .base_source import NewsSource
from datetime import datetime
import time
import random
from typing import List, Dict
import requests
import json

class XueqiuSource(NewsSource):
    """雪球新闻源"""
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.name = "雪球"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Origin': 'https://xueqiu.com',
            'Referer': 'https://xueqiu.com/',
            'Connection': 'keep-alive'
        }
        
    def fetch_news(self, limit: int = 100) -> List[Dict]:
        """获取雪球新闻"""
        try:
            # 获取雪球新闻API
            url = 'https://xueqiu.com/statuses/hot/listV2.json'
            params = {
                'since_id': -1,
                'max_id': -1,
                'size': limit
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data or 'items' not in data:
                if self.logger:
                    self.logger.warning("未获取到雪球新闻")
                return []
                
            news_list = []
            for item in data['items']:
                try:
                    title = item.get('title', '')
                    content = item.get('text', '')
                    created_at = item.get('created_at', '')
                    news_url = f"https://xueqiu.com{item.get('target', '')}"
                    
                    if not title or not content:
                        continue
                        
                    # 转换时间戳
                    if created_at:
                        news_time = datetime.fromtimestamp(created_at / 1000)
                    else:
                        news_time = datetime.now()
                        
                    news_list.append({
                        'title': title,
                        'content': content,
                        'time': news_time,
                        'url': news_url,
                        'source': self.name
                    })
                    
                    if len(news_list) >= limit:
                        break
                        
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"处理雪球新闻项时出错: {str(e)}")
                    continue
                    
            return news_list
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"获取雪球新闻失败: {str(e)}")
            return [] 