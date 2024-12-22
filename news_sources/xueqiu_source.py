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
        self.base_url = "https://xueqiu.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Origin': 'https://xueqiu.com',
            'Referer': 'https://xueqiu.com/',
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        self.session = requests.Session()
        
    def _init_session(self):
        """初始化会话，获取必要的Cookie"""
        try:
            # 访问首页获取Cookie
            response = self.session.get(
                self.base_url,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"初始化雪球会话失败: {str(e)}")
            return False
        
    def fetch_news(self, limit: int = 100) -> List[Dict]:
        """获取雪球新闻"""
        try:
            # 初始化会话
            if not self._init_session():
                return []
            
            # 获取新闻列表
            api_url = f"{self.base_url}/v4/statuses/public_timeline_by_category.json"
            params = {
                'category': '-1',
                'count': min(limit, 100),
                'source': 'all'
            }
            
            response = self.session.get(
                api_url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            # 检查响应内容
            if self.logger:
                self.logger.debug(f"雪球API响应: {response.text[:200]}...")
            
            data = response.json()
            if not data or 'list' not in data:
                if self.logger:
                    self.logger.warning("未获取到雪球新闻数据")
                return []
            
            news_list = []
            for item in data['list']:
                try:
                    # 提取文章内容
                    description = item.get('description', '')
                    title = item.get('title', description[:50] + '...' if description else '')
                    created_at = item.get('created_at', '')
                    
                    if not (title or description):
                        continue
                    
                    # 转换时间戳
                    if created_at:
                        news_time = datetime.fromtimestamp(created_at / 1000)
                    else:
                        news_time = datetime.now()
                    
                    news_list.append({
                        'title': title,
                        'content': description,
                        'time': news_time,
                        'url': f"{self.base_url}/statuses/{item.get('id', '')}",
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