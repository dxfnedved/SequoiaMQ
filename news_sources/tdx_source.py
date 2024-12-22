from .base_source import NewsSource
from datetime import datetime
import time
import random
from typing import List, Dict
import requests
from bs4 import BeautifulSoup

class TDXSource(NewsSource):
    """通达信新闻源"""
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.name = "通达信"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }
        self.session = requests.Session()
        
    def fetch_news(self, limit: int = 100) -> List[Dict]:
        """获取通达信新闻"""
        try:
            # 使用备用新闻源
            urls = [
                'https://www.cnstock.com/fastNews/10004',  # 上证快讯
                'https://www.cnstock.com/v_news/sns_jg/index.html'   # 机构资讯
            ]
            
            news_list = []
            for url in urls:
                try:
                    response = self.session.get(url, headers=self.headers, timeout=30)
                    response.raise_for_status()
                    
                    # 设置正确的编码
                    response.encoding = response.apparent_encoding or 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 查找新闻列表
                    news_items = soup.select('.new-list li')
                    
                    for item in news_items:
                        try:
                            if len(news_list) >= limit:
                                break
                                
                            # 获取新闻链接和标题
                            link = item.find('a')
                            if not link:
                                continue
                                
                            title = link.get_text().strip()
                            news_url = link.get('href', '')
                            if not news_url.startswith('http'):
                                news_url = 'https://www.cnstock.com' + news_url
                                
                            if not title or not news_url:
                                continue
                                
                            # 获取时间
                            time_elem = item.select_one('.time')
                            if time_elem:
                                time_text = time_elem.get_text().strip()
                                try:
                                    news_time = datetime.strptime(time_text, '%Y-%m-%d %H:%M')
                                except ValueError:
                                    news_time = datetime.now()
                            else:
                                news_time = datetime.now()
                                
                            # 获取新闻内容
                            content = self._get_news_content(news_url)
                            if not content:
                                continue
                                
                            news_list.append({
                                'title': title,
                                'content': content,
                                'time': news_time,
                                'url': news_url,
                                'source': self.name
                            })
                            
                            # 添加随机延时
                            time.sleep(random.uniform(0.5, 1.5))
                            
                        except Exception as e:
                            if self.logger:
                                self.logger.warning(f"处理新闻项时出错: {str(e)}")
                            continue
                            
                    if len(news_list) >= limit:
                        break
                        
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"获取新闻列表失败 {url}: {str(e)}")
                    continue
                    
            return news_list
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"获取通达信新闻失败: {str(e)}")
            return []
            
    def _get_news_content(self, url: str) -> str:
        """获取新闻内容"""
        try:
            response = self.session.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()
            
            # 设置正确的编码
            response.encoding = response.apparent_encoding or 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多个可能的内容选择器
            content_selectors = [
                '.article-content',
                '#qmt_content_div',
                '.content',
                '.article'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 移除脚本和样式
                    for script in content_elem.find_all(['script', 'style']):
                        script.decompose()
                    
                    # 获取文本内容
                    content = content_elem.get_text().strip()
                    # 清理空白字符
                    content = ' '.join(content.split())
                    return content
                    
            return ""
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"获取新闻内容失败 {url}: {str(e)}")
            return "" 