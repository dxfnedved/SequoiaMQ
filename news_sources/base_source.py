from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

class NewsSource(ABC):
    """新闻源基类"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.name = self.__class__.__name__
        
    @abstractmethod
    def fetch_news(self, limit: int = 100) -> List[Dict]:
        """获取新闻列表"""
        pass
        
    def clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not isinstance(text, str):
            return ""
        # 移除特殊字符和控制字符
        text = ''.join(char for char in text if ord(char) >= 32)
        return text.strip()
        
    def standardize_news(self, news_list: List[Dict]) -> pd.DataFrame:
        """标准化新闻数据"""
        try:
            if not news_list:
                return pd.DataFrame()
                
            # 转换为DataFrame
            df = pd.DataFrame(news_list)
            
            # 确保必要的列存在
            required_columns = ['title', 'content', 'time', 'source', 'url']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ''
                    
            # 清理文本内容
            df['title'] = df['title'].apply(self.clean_text)
            df['content'] = df['content'].apply(self.clean_text)
            
            # 标准化时间格式
            df['time'] = pd.to_datetime(df['time'])
            
            # 添加来源标识
            df['source'] = self.name
            
            # 删除空内容
            df = df.dropna(subset=['title', 'content'])
            
            # 按时间排序
            df = df.sort_values('time', ascending=False)
            
            return df
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"标准化新闻数据失败: {str(e)}")
            return pd.DataFrame() 