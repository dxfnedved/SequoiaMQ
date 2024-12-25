import pandas as pd
from typing import List, Dict
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import json
from .base_source import NewsSource

class SinaSource(NewsSource):
    """新浪财经新闻源"""
    
    def __init__(self, logger=None):
        super().__init__(name="新浪财经", logger=logger)
        self.api_url = "https://feed.mix.sina.com.cn/api/roll/get"
        
    def fetch_news(self, limit: int = 25) -> List[Dict]:
        """获取新浪财经新闻"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": "https://finance.sina.com.cn/"
            }
            
            params = {
                "pageid": "155",
                "lid": "1686",
                "num": limit,
                "page": 1,
                "encode": "utf-8"
            }
            
            response = requests.get(
                self.api_url,
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                self.logger.error(f"获取新浪财经新闻失败: HTTP {response.status_code}")
                return []
                
            data = response.json()
            if "result" not in data or "data" not in data["result"]:
                self.logger.error("新浪财经新闻数据格式错误")
                return []
                
            news_list = []
            for item in data["result"]["data"]:
                try:
                    # 获取新闻详情
                    content = self._fetch_news_content(item.get("url", ""))
                    news_time = datetime.strptime(
                        item.get("ctime", ""),
                        "%Y-%m-%d %H:%M:%S"
                    )
                except:
                    content = ""
                    news_time = datetime.now()
                    
                news = {
                    "title": item.get("title", ""),
                    "content": content,
                    "url": item.get("url", ""),
                    "time": news_time,
                    "source": self.name
                }
                news_list.append(news)
                
            return news_list
            
        except Exception as e:
            self.logger.error(f"获取新浪财经新闻出错: {str(e)}")
            return []
            
    def _fetch_news_content(self, url: str) -> str:
        """获取新闻详情内容"""
        try:
            if not url:
                return ""
                
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = response.apparent_encoding
            
            if response.status_code != 200:
                return ""
                
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 尝试不同的文章内容选择器
            content_selectors = [
                "div.article p",  # 标准文章
                "div#artibody p",  # 老式文章
                "div.article-content p"  # 新式文章
            ]
            
            content = []
            for selector in content_selectors:
                paragraphs = soup.select(selector)
                if paragraphs:
                    content = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
                    break
                    
            return "\n".join(content)
            
        except Exception as e:
            self.logger.error(f"获取新闻详情失败: {str(e)}")
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
            self.logger.error(f"标准化新浪财经新闻数据出错: {str(e)}")
            return pd.DataFrame() 