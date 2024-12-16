import os
import json
import pandas as pd
from datetime import datetime
import akshare as ak
from pypinyin import lazy_pinyin, Style
from logger_manager import LoggerManager
from utils import is_stock_active

class StockCache:
    """股票信息缓存管理器"""
    
    def __init__(self, logger_manager=None):
        self.logger_manager = logger_manager or LoggerManager()
        self.logger = self.logger_manager.get_logger("stock_cache")
        self.cache_dir = "cache"
        self.ensure_cache_dir()
        
    def ensure_cache_dir(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
    def get_cache_path(self):
        """获取当天的缓存文件路径"""
        today = datetime.now().strftime('%Y%m%d')
        return os.path.join(self.cache_dir, f'stock_list_{today}.json')
        
    def load_stock_list(self):
        """加载股票列表（优先从缓存加载）"""
        try:
            cache_path = self.get_cache_path()
            
            # 检查是否存在当天的缓存
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    df = pd.DataFrame(data)
                    
                    # 验证缓存中的股票是否仍然有效
                    valid_stocks = []
                    for _, row in df.iterrows():
                        if is_stock_active(row['code'], row['name']):
                            valid_stocks.append(row)
                        else:
                            self.logger.warning(f"股票 {row['code']} - {row['name']} 已不再交易，从缓存中移除")
                    
                    df = pd.DataFrame(valid_stocks)
                    if not df.empty:
                        self.logger.info(f"从缓存加载了 {len(df)} 只有效股票信息")
                        return df
                    else:
                        self.logger.warning("缓存中没有有效股票，重新获取")
            
            # 如果没有缓存或缓存无效，从网络获取
            df = ak.stock_info_a_code_name()
            
            # 添加拼音列
            df['pinyin'] = df['name'].apply(lambda x: ''.join(lazy_pinyin(x)))  # 全拼
            df['pinyin_initials'] = df['name'].apply(
                lambda x: ''.join(lazy_pinyin(x, style=Style.FIRST_LETTER))  # 首字母
            )
            
            # 过滤条件
            def is_valid_stock(code, name):
                # 排除ST股票
                if 'ST' in name.upper():
                    return False
                # 排除退市股票
                if '退' in name:
                    return False
                # 排除科创板股票
                if code.startswith('688'):
                    return False
                # 排除北交所股票
                if code.startswith('8'):
                    return False
                # 只保留沪深主板、中小板、创业板
                if not code.startswith(('000', '001', '002', '003', '300', '600', '601', '603', '605')):
                    return False
                # 检查是否正常交易
                return is_stock_active(code, name)
            
            # 应用过滤
            df = df[df.apply(lambda x: is_valid_stock(x['code'], x['name']), axis=1)]
            
            # 保存到缓存
            df.to_json(cache_path, orient='records', force_ascii=False)
            self.logger.info(f"成功获取并缓存 {len(df)} 只有效股票信息")
            
            return df
            
        except Exception as e:
            self.logger.error(f"加载股票列表失败: {str(e)}")
            return pd.DataFrame(columns=['code', 'name', 'pinyin', 'pinyin_initials'])
            
    def clear_cache(self):
        """清除缓存"""
        try:
            cache_path = self.get_cache_path()
            if os.path.exists(cache_path):
                os.remove(cache_path)
                self.logger.info("已清除股票列表缓存")
        except Exception as e:
            self.logger.error(f"清除缓存失败: {str(e)}")

# 创建全局实例
stock_cache = StockCache() 