import pandas as pd
from datetime import datetime, timedelta
import time
import random
from logger_manager import LoggerManager
import traceback
import os
import requests
from bs4 import BeautifulSoup
import json

class NewsCrawler:
    """新闻爬虫类 - 使用备用数据源和请求方式"""
    def __init__(self, logger_manager=None):
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("news_crawler")
        self.max_news = 100  # 最大新闻数量
        self.max_retries = 3  # 最大重试次数
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }
        
    def get_sina_finance_news(self, retries=0):
        """获取新浪财经新闻（备用数据源）"""
        try:
            news_list = []
            url = 'https://finance.sina.com.cn/roll/index.d.html'
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # 设置正确的编码
            response.encoding = response.apparent_encoding or 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找新闻列表
            news_items = soup.select('.list_009 li')
            self.logger.info(f"找到 {len(news_items)} 条新闻")
            
            for item in news_items[:self.max_news]:
                try:
                    link_elem = item.find('a')
                    if not link_elem:
                        continue
                        
                    title = link_elem.get_text().strip()
                    link = link_elem.get('href', '')
                    time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 获取新闻内容
                    content = self._get_news_content_requests(link)
                    
                    if content:
                        # 确保所有字段都是UTF-8编码
                        title = title.encode('utf-8', errors='ignore').decode('utf-8')
                        content = content.encode('utf-8', errors='ignore').decode('utf-8')
                        
                        news_list.append({
                            'title': title,
                            'url': link,
                            'time': time_str,
                            'content': content,
                            'source': '新浪财经'
                        })
                        
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    self.logger.warning(f"解析新闻项时出错: {str(e)}")
                    continue
                    
            return news_list
            
        except Exception as e:
            self.logger.error(f"获取新浪财经新闻失败: {str(e)}")
            if retries < self.max_retries:
                time.sleep(random.uniform(2, 5))
                return self.get_sina_finance_news(retries + 1)
            return []
            
    def _get_news_content_requests(self, url):
        """使用 requests 获取新闻内容"""
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()
            
            # 设置正确的编码
            response.encoding = response.apparent_encoding or 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多个可能的内容选择器
            content_selectors = [
                '.article-content',
                '#artibody',
                '.article',
                '.content',
                '.main-content'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text().strip()
                    # 确保内容是UTF-8编码
                    content = content.encode('utf-8', errors='ignore').decode('utf-8')
                    break
                    
            return content
            
        except Exception as e:
            self.logger.warning(f"获取新闻内容失败 {url}: {str(e)}")
            return ""
            
    def get_all_news(self):
        """获取所有新闻"""
        try:
            # 尝试获取新浪财经新闻
            all_news = self.get_sina_finance_news()
            
            if not all_news:
                self.logger.warning("未获取到任何新闻，使用模拟数据")
                # 生成模拟数据以确保功能可用
                all_news = self._generate_mock_news()
                
            # 转换为DataFrame
            news_df = pd.DataFrame(all_news)
            if not news_df.empty:
                # 标准化时间格式
                news_df['time'] = pd.to_datetime(news_df['time'])
                # 删除无效的时间记录
                news_df = news_df.dropna(subset=['time'])
                # 按时间排序
                news_df = news_df.sort_values('time', ascending=False)
                
                self.logger.info(f"成功获取 {len(news_df)} 条新闻")
                return news_df
            
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"获取所有新闻失败: {str(e)}")
            self.logger.error(traceback.format_exc())
            return pd.DataFrame()
            
    def _generate_mock_news(self):
        """生成模拟新闻数据"""
        mock_news = []
        current_time = datetime.now()
        
        # 预定义一些模拟新闻标题和内容
        templates = [
            {
                'title': '市场情绪稳定，A股震荡整理',
                'content': '今日A股市场维持震荡整理态势，成交量保持平稳。机构分析认为，市场短期仍以结构性机会为主。'
            },
            {
                'title': '科技板块表现活跃，芯片股持续走强',
                'content': '科技板块今日表现抢眼，特别是芯片产业链相关个股，多只个股录得较大涨幅。分析师认为，科技创新仍是市场主线。'
            },
            {
                'title': '央行强调保持流动性合理充裕',
                'content': '央行今日表示将继续实施稳健的货币政策，保持流动性合理充裕，促进经济高质量发展。'
            }
        ]
        
        # 生成多条模拟新闻
        for i in range(10):
            template = random.choice(templates)
            news_time = current_time - timedelta(hours=random.randint(0, 24))
            
            mock_news.append({
                'title': template['title'],
                'url': 'https://example.com/news',
                'time': news_time.strftime('%Y-%m-%d %H:%M:%S'),
                'content': template['content'],
                'source': '模拟数据'
            })
            
        return mock_news
            
    def save_news_cache(self, news_df, cache_file):
        """保存新闻缓存"""
        try:
            if news_df.empty:
                self.logger.warning("没有新闻数据可供缓存")
                return False
                
            # 确保缓存目录存在
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            
            news_df.to_json(cache_file, orient='records', force_ascii=False)
            self.logger.info(f"新闻缓存已保存到: {cache_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存新闻缓存失败: {str(e)}")
            return False
            
    def load_news_cache(self, cache_file):
        """加载新闻缓存"""
        try:
            if not os.path.exists(cache_file):
                self.logger.info("新闻缓存文件不存在")
                return None
                
            # 检查缓存是否过期（2小时）
            if time.time() - os.path.getmtime(cache_file) > 7200:
                self.logger.info("新闻缓存已过期")
                return None
                
            news_df = pd.read_json(cache_file, orient='records')
            news_df['time'] = pd.to_datetime(news_df['time'])
            
            if not news_df.empty:
                self.logger.info(f"从缓存加载了 {len(news_df)} 条新闻")
                return news_df
            
            return None
            
        except Exception as e:
            self.logger.error(f"加载新闻缓存失败: {str(e)}")
            return None 