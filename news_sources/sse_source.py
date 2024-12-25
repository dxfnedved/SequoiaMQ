from bs4 import BeautifulSoup
import pandas as pd
from typing import List, Dict
import logging
from datetime import datetime
import requests
import json
from .base_source import NewsSource
import time

class SSESource(NewsSource):
    """上海证券交易所新闻源"""
    
    def __init__(self, logger=None):
        super().__init__(name="上交所", logger=logger)
        self.base_url = "http://www.sse.com.cn"
        self.api_url = "https://www.sse.com.cn/home/component/news/"
        
    def fetch_news(self, limit: int = 25) -> List[Dict]:
        """获取上交所新闻"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            # 首先访问主页获取必要的Cookie
            session = requests.Session()
            session.get(self.base_url, headers=headers, timeout=10)
            
            # 获取新闻列表
            response = session.get(
                self.api_url,
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                self.logger.error(f"获取上交所新闻失败: HTTP {response.status_code}")
                return []
                
            # 使用BeautifulSoup解析HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_list = []
            news_items = soup.select('.sse_list_1 dl')
            
            for item in news_items[:limit]:
                try:
                    # 获取标题和链接
                    title_elem = item.find('a')
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text().strip()
                    url = title_elem.get('href', '')
                    if url and not url.startswith('http'):
                        url = f"{self.base_url}{url}"
                        
                    # 获取时间
                    date_elem = item.select_one('.date')
                    if date_elem:
                        try:
                            news_time = datetime.strptime(
                                date_elem.get_text().strip(),
                                '%Y-%m-%d'
                            )
                        except:
                            news_time = datetime.now()
                    else:
                        news_time = datetime.now()
                        
                    # 获取新闻内容
                    content = self._get_news_content(url, session, headers)
                    
                    if title and content:
                        news_list.append({
                            'title': title,
                            'content': content,
                            'url': url,
                            'time': news_time,
                            'source': self.name
                        })
                        
                    # 添加延时避免请求过快
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.warning(f"处理新闻项时出错: {str(e)}")
                    continue
                    
            return news_list
            
        except Exception as e:
            self.logger.error(f"获取上交所新闻出错: {str(e)}")
            return []
            
    def _get_news_content(self, url: str, session: requests.Session, headers: dict) -> str:
        """获取新闻内容"""
        try:
            response = session.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return ""
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多个可能的内容选择器
            content_selectors = [
                '.allZoom',  # 主要内容区
                '.article-content',  # 文章内容
                '.content'  # 通用内容
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 移除脚本和样式
                    for script in content_elem.find_all(['script', 'style']):
                        script.decompose()
                        
                    # 获取所有段落文本
                    paragraphs = content_elem.find_all('p')
                    if paragraphs:
                        return '\n'.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
                    else:
                        return content_elem.get_text().strip()
                        
            return ""
            
        except Exception as e:
            self.logger.warning(f"获取新闻内���失败 {url}: {str(e)}")
            return ""
            
    def standardize_news(self, news_list: List[Dict]) -> pd.DataFrame:
        """标准化新闻数据"""
        try:
            if not news_list:
                return pd.DataFrame()
                
            df = pd.DataFrame(news_list)
            
            # 确保所有必需的列都存在
            required_columns = ["title", "content", "url", "time", "source"]
            for col in required_columns:
                if col not in df.columns:
                    df[col] = None
                    
            # 确保时间列的格式正确
            df["time"] = pd.to_datetime(df["time"])
            
            return df[required_columns]
            
        except Exception as e:
            self.logger.error(f"标准化上交所新闻数据出错: {str(e)}")
            return pd.DataFrame() 