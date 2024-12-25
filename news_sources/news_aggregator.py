import pandas as pd
from typing import List
from datetime import datetime
import logging
from .tonghuashun_source import TonghuashunSource
from .eastmoney_source import EastmoneySource
from .sse_source import SSESource
from .szse_source import SZSESource
from .sina_source import SinaSource

class NewsAggregator:
    """新闻聚合器"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.sources = [
            # SSESource(logger),      # 上交所新闻
            SZSESource(logger),     # 深交所新闻
            SinaSource(logger),     # 新浪财经新闻
            EastmoneySource(logger) # 东方财富新闻
        ]
        
    def get_news(self, limit_per_source: int = 25) -> pd.DataFrame:
        """获取所有来源的新闻"""
        try:
            all_news = []
            
            # 从每个来源获取新闻
            for source in self.sources:
                try:
                    news_list = source.fetch_news(limit_per_source)
                    if news_list:
                        # 标准化新闻数据
                        news_df = source.standardize_news(news_list)
                        if not news_df.empty:
                            all_news.append(news_df)
                            self.logger.info(f"从 {source.name} 获取到 {len(news_df)} 条新闻")
                            
                except Exception as e:
                    self.logger.error(f"从 {source.name} 获取新闻失败: {str(e)}")
                    continue
                    
            if not all_news:
                self.logger.warning("未从任何来源获取到新闻")
                return pd.DataFrame()
                
            # 合并所有新闻
            news_df = pd.concat(all_news, ignore_index=True)
            
            # 删除重复的新闻（基于标题）
            news_df = news_df.drop_duplicates(subset=['title'], keep='first')
            
            # 按时间排序
            news_df = news_df.sort_values('time', ascending=False)
            
            # 重置索引
            news_df = news_df.reset_index(drop=True)
            
            self.logger.info(f"成功获取 {len(news_df)} 条新闻")
            return news_df
            
        except Exception as e:
            self.logger.error(f"获取新闻失败: {str(e)}")
            return pd.DataFrame() 