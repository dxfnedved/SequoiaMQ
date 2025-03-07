import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
import re
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random
import traceback
import akshare as ak
import json
import html

class NewsCrawler:
    """新闻爬取器"""
    
    def __init__(self):
        self.logger = logger.bind(name="news_crawler")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        # 初始化股票代码缓存
        self._stock_code_cache = {}
        self._init_stock_code_cache()
        
    def _init_stock_code_cache(self):
        """初始化股票代码缓存"""
        try:
            # 获取A股列表
            stock_list = ak.stock_info_a_code_name()
            
            # 构建缓存字典
            for _, row in stock_list.iterrows():
                code = row['code']
                name = row['name']
                # 添加带市场前缀的代码
                if code.startswith('6'):
                    self._stock_code_cache[code] = {'name': name, 'full_code': f'sh{code}'}
                else:
                    self._stock_code_cache[code] = {'name': name, 'full_code': f'sz{code}'}
                # 添加名称到代码的映射
                self._stock_code_cache[name] = {'code': code, 'full_code': self._stock_code_cache[code]['full_code']}
                
            self.logger.info(f"股票代码缓存初始化完成，共加载 {len(stock_list)} 只股票")
            
        except Exception as e:
            self.logger.error(f"初始化股票代码缓存失败: {str(e)}")
            self.logger.debug(f"错误详情:\n{traceback.format_exc()}")
            
    def _get_full_stock_code(self, code_or_name: str) -> str:
        """获取完整的股票代码（带市场前缀）
        
        Args:
            code_or_name: 股票代码或名称
        Returns:
            str: 带市场前缀的股票代码
        """
        # 如果已经带有前缀，直接返回
        if code_or_name.startswith(('sh', 'sz')):
            return code_or_name
            
        # 从缓存中查找
        if code_or_name in self._stock_code_cache:
            return self._stock_code_cache[code_or_name]['full_code']
            
        # 如果是6位数字，尝试判断市场
        if code_or_name.isdigit() and len(code_or_name) == 6:
            if code_or_name.startswith('6'):
                return f'sh{code_or_name}'
            else:
                return f'sz{code_or_name}'
                
        return ""
        
    def _get_stock_name(self, stock_code: str, log_output: bool = True) -> str:
        """从缓存获取股票简称
        
        Args:
            stock_code: 股票代码（可能带有sh/sz前缀）
            log_output: 是否输出日志，默认为True
        Returns:
            str: 股票简称
        """
        try:
            # 移除可能存在的市场前缀
            pure_code = stock_code.replace('sh', '').replace('sz', '')
            
            # 从缓存中查找
            if pure_code in self._stock_code_cache:
                stock_name = self._stock_code_cache[pure_code]['name']
                if log_output:
                    self.logger.info(f"获取到股票简称: {stock_name}")
                return stock_name
                
            # 如果缓存中没有，尝试从akshare获取
            stock_info = ak.stock_individual_info_em(symbol=pure_code)
            if not stock_info.empty:
                name_row = stock_info[stock_info['item'].str.contains('简称', na=False)]
                if not name_row.empty:
                    stock_name = name_row.iloc[0]['value']
                    # 更新缓存
                    self._stock_code_cache[pure_code] = {
                        'name': stock_name,
                        'full_code': stock_code if stock_code.startswith(('sh', 'sz')) else f"{'sh' if pure_code.startswith('6') else 'sz'}{pure_code}"
                    }
                    self._stock_code_cache[stock_name] = {
                        'code': pure_code,
                        'full_code': self._stock_code_cache[pure_code]['full_code']
                    }
                    if log_output:
                        self.logger.info(f"获取到股票简称: {stock_name}")
                    return stock_name
                    
            self.logger.warning(f"未找到股票 {stock_code} 的信息")
            return ""
            
        except Exception as e:
            self.logger.error(f"获取股票简称失败: {str(e)}")
            self.logger.debug(f"错误详情:\n{traceback.format_exc()}")
            return ""
        
    def get_company_news(self, stock_code: str, days: int = 7) -> pd.DataFrame:
        """获取指定公司的新闻
        Args:
            stock_code: 股票代码
            days: 获取最近几天的新闻，默认7天
        Returns:
            pd.DataFrame: 包含新闻数据的DataFrame
        """
        try:
            # 获取标准股票简称
            company_name = self._get_stock_name(stock_code)
            if not company_name:
                self.logger.error(f"无法获取股票 {stock_code} 的简称")
                return pd.DataFrame()
            
            news_list = []
            page = 1
            max_pages = 3  # 最多获取3页
            
            while page <= max_pages:
                # 构建请求参数
                params = {
                    'cb': f'jQuery{int(time.time() * 1000)}_{int(time.time() * 1000)}',
                    'param': json.dumps({
                        'uid': '',
                        'keyword': company_name,
                        'type': ['cmsArticleWebOld'],
                        'client': 'web',
                        'clientType': 'web',
                        'clientVersion': 'curr',
                        'param': {
                            'cmsArticleWebOld': {
                                'searchScope': 'default',
                                'sort': 'default',
                                'pageIndex': page,
                                'pageSize': 20,
                                'preTag': '<em>',
                                'postTag': '</em>'
                            }
                        }
                    }),
                    '_': int(time.time() * 1000)
                }
                
                # 设置请求头
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Referer': 'https://so.eastmoney.com/',
                    'Cookie': 'qgqp_b_id=5a6a256b677058a6ce40ecf0d4a50b1d; st_si=87177108332606; emshistory=%5B%22%E5%88%9B%E4%B8%9A%E9%BB%91%E9%A9%AC%22%2C%22%E7%91%9E%E7%8E%9B%E7%B2%BE%E5%AF%86%22%2C%22%E5%A4%A9%E5%88%A9%E7%A7%91%E6%8A%80%22%2C%22%E5%8F%8B%E8%AE%AF%E8%BE%BE%22%2C%22%E9%9B%AA%E6%A6%95%E7%94%9F%E7%89%A9%22%5D; fullscreengg=1; fullscreengg2=1; websitepoptg_api_time=1739434885219; st_asi=delete; st_pvi=95181513330632; st_sp=2024-12-05%2016%3A36%3A48; st_inirUrl=https%3A%2F%2Fwww.eastmoney.com%2F; st_sn=53; st_psi=2025021414152940-118000300904-6288456257'
                }
                
                try:
                    # 发送请求
                    url = 'https://search-api-web.eastmoney.com/search/jsonp'
                    response = requests.get(url, params=params, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    # 解析JSONP响应
                    jsonp_text = response.text
                    json_text = re.search(r'jQuery\d+_\d+\((.*?)\)$', jsonp_text, re.DOTALL).group(1)
                    data = json.loads(json_text)
                    
                    # 提取新闻列表
                    if data.get('result', {}).get('cmsArticleWebOld'):
                        items = data['result']['cmsArticleWebOld']
                        if not items:  # 如果没有更多新闻，退出循环
                            break
                            
                        for item in items:
                            try:
                                # 移除HTML标签
                                title = re.sub(r'<[^>]+>', '', item.get('title', ''))
                                content = re.sub(r'<[^>]+>', '', item.get('content', ''))
                                
                                # 放宽过滤条件，只要标题或内容中包含股票代码或公司名称即可
                                if company_name in title or company_name in content or stock_code in title or stock_code in content:
                                    news_list.append({
                                        'title': title,
                                        'content': content,
                                        'source': item.get('mediaName', '东方财富网'),
                                        'time': item.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                                    })
                            except Exception as e:
                                self.logger.warning(f"解析新闻项失败: {str(e)}")
                                continue
                    else:
                        break
                        
                    page += 1
                    time.sleep(1)  # 添加延时避免请求过快
                    
                except Exception as e:
                    self.logger.error(f"获取第{page}页新闻失败: {str(e)}")
                    break
            
            # 转换为DataFrame
            df = pd.DataFrame(news_list)
            if not df.empty:
                # 转换时间列
                df['time'] = pd.to_datetime(df['time'])
                # 过滤最近n天的新闻
                cutoff_date = datetime.now() - timedelta(days=days)
                df = df[df['time'] >= cutoff_date]
                
                # 按时间降序排序
                df = df.sort_values('time', ascending=False)
                # 应用去重逻辑
                df = self._remove_duplicates(df)
                
                self.logger.info(f"成功获取{len(df)}条相关新闻")
            else:
                self.logger.warning(f"未找到与{company_name}({stock_code})相关的新闻")
                
            return df
            
        except Exception as e:
            self.logger.error(f"获取公司新闻失败 {stock_code}: {str(e)}")
            self.logger.debug(f"错误详情:\n{traceback.format_exc()}")
            return pd.DataFrame()
            
    def get_all_news(self) -> pd.DataFrame:
        """获取所有股票新闻（保留此方法以保持向后兼容）"""
        try:
            # 获取东方财富网财经新闻首页的新闻
            url = 'https://finance.eastmoney.com/'
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_list = []
            
            # 获取首页新闻
            news_items = soup.select('.news-item')[:20]  # 获取前20条新闻
            
            for item in news_items:
                try:
                    title = item.select_one('.news-item_title').get_text(strip=True)
                    content = item.select_one('.news-item_content').get_text(strip=True)
                    source = item.select_one('.news-item_source').get_text(strip=True)
                    news_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    news_list.append({
                        'title': title,
                        'content': content,
                        'source': source,
                        'time': news_time
                    })
                except Exception as e:
                    self.logger.warning(f"解析新闻项失败: {str(e)}")
                    continue
                    
            return pd.DataFrame(news_list)
        except Exception as e:
            self.logger.error(f"获取新闻失败: {str(e)}")
            return pd.DataFrame() 

    def _clean_html_entities(self, text: str) -> str:
        """清理HTML实体编码
        
        Args:
            text: 包含HTML实体的文本
        Returns:
            str: 清理后的文本
        """
        try:
            if not text:
                return text
                
            # 处理 \u003cem\u003e 这样的 unicode 转义
            # 先尝试直接解码
            try:
                text = text.encode('latin1').decode('unicode_escape')
            except Exception:
                # 如果失败，尝试使用正则表达式替换
                text = re.sub(r'\\u003c(.*?)\\u003e', '', text)
            
            # 移除HTML标签
            text = re.sub(r'<[^>]+>', '', text)
            
            # 处理可能的其他HTML实体
            text = html.unescape(text)
            
            return text.strip()
        except Exception as e:
            self.logger.warning(f"清理HTML实体失败: {str(e)}")
            return text

    def get_cls_news(self, stock_code: str, stock_name: str = None, days: int = 5) -> pd.DataFrame:
        """获取财联社新闻
        
        Args:
            stock_code: 股票代码
            stock_name: 股票简称，如果为None则会重新获取
            days: 获取最近几天的新闻，默认5天
        """
        try:
            # 如果没有传入股票简称，则获取（不输出日志）
            if stock_name is None:
                stock_name = self._get_stock_name(stock_code, log_output=False)
                
            news_list = []
            
            # 基础请求配置
            base_headers = {
                **self.headers,
                'Content-Type': 'application/json;charset=UTF-8',
                'Origin': 'https://www.cls.cn',
                'Cookie': 'HWWAFSESID=ebe8efddbdc9cbc5d5; HWWAFSESTIME=1737085658805; hasTelegraphNotification=on; hasTelegraphRemind=on; hasTelegraphSound=on'
            }
            
            base_params = {
                'app': 'CailianpressWeb',
                'os': 'web',
                'sv': '8.4.6',
                'sign': '9f8797a1f4de66c2370f7a03990d2737'
            }
            
            # 获取电报新闻
            try:
                telegram_headers = {
                    **base_headers,
                    'Referer': f'https://www.cls.cn/searchPage?keyword={urllib.parse.quote(stock_name)}&type=telegram'
                }
                
                telegram_data = {
                    'type': 'telegram',
                    'keyword': stock_name,
                    'page': 0,
                    'rn': 20,
                    'os': 'web',
                    'sv': '8.4.6',
                    'app': 'CailianpressWeb'
                }
                
                response = requests.post(
                    'https://www.cls.cn/api/sw',
                    headers=telegram_headers,
                    params=base_params,
                    json=telegram_data,
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get('errno') == 0 and 'telegram' in result.get('data', {}):
                    telegram_items = result['data']['telegram'].get('data', [])
                    for item in telegram_items:
                        # 清理标题和内容中的HTML实体
                        content = self._clean_html_entities(item.get('descr', ''))
                        
                        # 提取时间戳
                        news_time = datetime.fromtimestamp(item.get('time', time.time()))
                        # 检查是否在指定天数范围内
                        if (datetime.now() - news_time).days <= days:
                            news_list.append({
                                'title': '财联社电报',  # 电报类型的新闻通常没有标题
                                'content': content,
                                'source': '财联社',
                                'time': news_time,
                                'type': '电报'
                            })
                
            except Exception as e:
                self.logger.error(f"获取财联社电报失败: {str(e)}")
                
            # 获取资讯新闻
            try:
                depth_headers = {
                    **base_headers,
                    'Referer': f'https://www.cls.cn/searchPage?keyword={urllib.parse.quote(stock_name)}&type=depth'
                }
                
                depth_data = {
                    'type': 'depth',
                    'keyword': stock_name,
                    'page': 0,
                    'rn': 20,
                    'os': 'web',
                    'sv': '8.4.6',
                    'app': 'CailianpressWeb'
                }
                
                response = requests.post(
                    'https://www.cls.cn/api/sw',
                    headers=depth_headers,
                    params=base_params,
                    json=depth_data,
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get('errno') == 0 and 'depth' in result.get('data', {}):
                    depth_items = result['data']['depth'].get('data', [])
                    for item in depth_items:
                        # 清理标题和内容中的HTML实体
                        title = self._clean_html_entities(item.get('title', ''))
                        content = self._clean_html_entities(item.get('descr', ''))
                        
                        # 提取时间戳
                        news_time = datetime.fromtimestamp(item.get('time', time.time()))
                        # 检查是否在指定天数范围内
                        if (datetime.now() - news_time).days <= days:
                            news_list.append({
                                'title': title,
                                'content': content,
                                'source': '财联社',
                                'time': news_time,
                                'type': '资讯'
                            })
                
            except Exception as e:
                self.logger.error(f"获取财联社资讯失败: {str(e)}")
                
            df = pd.DataFrame(news_list)
            if not df.empty:
                df = df.sort_values('time', ascending=False)
                # 应用去重逻辑
                df = self._remove_duplicates(df)
                
                # 打印新闻类型统计
                self.logger.info(f"\n=== 财联社新闻类型统计 ===")
                self.logger.info(f"总计获取{len(df)}条新闻")
                self.logger.info(f"新闻类型分布:\n{df['type'].value_counts()}")
                
            return df
            
        except Exception as e:
            self.logger.error(f"获取财联社新闻失败: {str(e)}")
            return pd.DataFrame()
            
    def get_wind_news(self, stock_code: str, stock_name: str = None) -> pd.DataFrame:
        """获取万得新闻
        
        Args:
            stock_code: 股票代码
            stock_name: 股票简称，如果为None则会重新获取
        """
        try:
            # 如果没有传入股票简称，则获取（不输出日志）
            if stock_name is None:
                stock_name = self._get_stock_name(stock_code, log_output=False)
                
            news_list = []
            
            # 获取重要新闻
            try:
                url = 'https://www.wind.com.cn/Wind.Portal.App/insights/fetchImportantInsight'
                params = {'v': str(random.random())}
                headers = {
                    **self.headers,
                    'Content-Type': 'application/json;charset=UTF-8',
                    'Origin': 'https://www.wind.com.cn',
                    'Referer': 'https://www.wind.com.cn/portal/insights/index.html',
                    'Cookie': 'JSESSIONID=84EB21771D33632553DB6B291826172E; _ga=GA1.1.1705483737442.1705483737442; _ga_XECTB7VVLQ=GS1.1.1705483737.1.1.1705483737.0.0.0'
                }
                
                response = requests.post(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                
                # 检查响应内容是否为空
                if not response.text.strip():
                    self.logger.warning("万得API返回空响应")
                    return pd.DataFrame()
                    
                try:
                    result = response.json()
                except json.JSONDecodeError as e:
                    self.logger.error(f"万得API返回的数据不是有效的JSON格式: {str(e)}")
                    self.logger.debug(f"响应内容: {response.text[:200]}...")  # 只记录前200个字符
                    return pd.DataFrame()
                
                if result.get('success') and result.get('data', {}).get('response', {}).get('result', {}).get('docs'):
                    for item in result['data']['response']['result']['docs']:
                        try:
                            # 处理时间格式 '2025-01-17T06:16:50Z'
                            date_str = item['date'][0].replace('T', ' ').replace('Z', '')
                            news_time = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                            news_list.append({
                                'title': item['title'][0],
                                'content': item['abstract'][0],
                                'source': '万得',
                                'time': news_time,
                                'type': '头条新闻'  # 标记新闻类型
                            })
                        except Exception as e:
                            self.logger.warning(f"解析万得新闻时间失败: {str(e)}")
                            continue
                
                # 获取普通新闻列表
                url = 'https://www.wind.com.cn/Wind.Portal.App/insights/fetchInsights'
                params = {
                    'pageNum': 1,
                    'pageSize': 20,
                    'v': str(random.random())
                }
                
                response = requests.post(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                
                # 检查响应内容是否为空
                if not response.text.strip():
                    self.logger.warning("万得普通新闻API返回空响应")
                    return pd.DataFrame()
                    
                try:
                    result = response.json()
                except json.JSONDecodeError as e:
                    self.logger.error(f"万得普通新闻API返回的数据不是有效的JSON格式: {str(e)}")
                    self.logger.debug(f"响应内容: {response.text[:200]}...")  # 只记录前200个字符
                    return pd.DataFrame()
                
                if result.get('success') and result.get('data', {}).get('response', {}).get('result', {}).get('docs'):
                    for item in result['data']['response']['result']['docs']:
                        try:
                            # 处理时间格式 '2025-01-17T06:16:50Z'
                            date_str = item['date'][0].replace('T', ' ').replace('Z', '')
                            news_time = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                            news_list.append({
                                'title': item['title'][0],
                                'content': item['abstract'][0],
                                'source': '万得',
                                'time': news_time,
                                'type': '焦点新闻'  # 标记新闻类型
                            })
                        except Exception as e:
                            self.logger.warning(f"解析万得新闻时间失败: {str(e)}")
                            continue
                
            except Exception as e:
                self.logger.error(f"获取万得新闻失败: {str(e)}")
                
            df = pd.DataFrame(news_list)
            if not df.empty:
                df = df.sort_values('time', ascending=False)
                df = self._remove_duplicates(df)
                
            return df
            
        except Exception as e:
            self.logger.error(f"获取万得新闻失败: {str(e)}")
            return pd.DataFrame()
            
    def get_aggregated_news(self, code_or_name: str) -> pd.DataFrame:
        """获取聚合新闻
        
        整合东方财富、财联社和万得的新闻
        
        Args:
            code_or_name: 股票代码或名称
        """
        try:
            # 获取完整股票代码
            stock_code = self._get_full_stock_code(code_or_name)
            if not stock_code:
                self.logger.error(f"无法获取股票代码: {code_or_name}")
                return pd.DataFrame()
            
            # 获取股票简称 - 只在这里输出日志
            stock_name = self._get_stock_name(stock_code, log_output=True)
            
            # 获取各个来源的新闻
            df_eastmoney = self.get_company_news(stock_code)
            df_cls = self.get_cls_news(stock_code, stock_name=stock_name)
            df_wind = self.get_wind_news(stock_code, stock_name=stock_name)
            
            # 合并新闻
            df_list = []
            if not df_eastmoney.empty:
                df_list.append(df_eastmoney)
            if not df_cls.empty:
                df_list.append(df_cls)
            if not df_wind.empty:
                df_list.append(df_wind)
                
            if not df_list:
                self.logger.warning("未获取到任何新闻")
                return pd.DataFrame()
                
            df = pd.concat(df_list, ignore_index=True)
            
            # 按时间排序
            df = df.sort_values('time', ascending=False)
            
            # 去重
            df = self._remove_duplicates(df)
            
            # 输出新闻摘要
            self._print_news_summary(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取聚合新闻失败: {str(e)}")
            self.logger.debug(f"错误详情:\n{traceback.format_exc()}")
            return pd.DataFrame()
            
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """去除重复的新闻"""
        try:
            if df.empty:
                return df
                
            self.logger.debug(f"去重前数据量: {len(df)}")
            self.logger.debug(f"数据列: {df.columns.tolist()}")
            
            # 确保必要的列存在
            required_cols = ['title', 'content', 'time']  # 使用time而不是publish_time
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                self.logger.warning(f"缺少必要的列: {missing_cols}")
                return df
            
            # 记录去重前的数据分布
            self.logger.debug(f"去重前新闻来源分布:\n{df['source'].value_counts()}")
            if 'type' in df.columns:
                self.logger.debug(f"去重前新闻类型分布:\n{df['type'].value_counts()}")
            
            # 基于标题和内容的相似度去重
            df['title_content'] = df['title'] + df['content']
            df = df.sort_values('time', ascending=False)
            
            # 使用drop_duplicates替代可能有问题的索引操作
            df = df.drop_duplicates(subset=['title_content'], keep='first')
            
            # 删除临时列
            df = df.drop('title_content', axis=1)
            
            # 记录去重后的数据分布
            self.logger.debug(f"去重后数据量: {len(df)}")
            self.logger.debug(f"去重后新闻来源分布:\n{df['source'].value_counts()}")
            if 'type' in df.columns:
                self.logger.debug(f"去重后新闻类型分布:\n{df['type'].value_counts()}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"去重失败: {str(e)}")
            self.logger.debug(f"错误详情:\n{traceback.format_exc()}")
            # 发生错误时返回原始数据
            return df

    def _print_news_summary(self, df: pd.DataFrame):
        """打印新闻摘要
        
        Args:
            df: 包含新闻数据的DataFrame
        """
        if df.empty:
            self.logger.warning("未获取到任何新闻")
            return
            
        # 按来源分组打印新闻摘要
        self.logger.info("\n=== 东方财富新闻摘要 ===")
        eastmoney_news = df[df['source'] == '东方财富网']
        if not eastmoney_news.empty:
            for _, row in eastmoney_news.iterrows():
                self.logger.info(f"[{row['time'].strftime('%Y-%m-%d %H:%M:%S')}] {row['title']}")
                
        self.logger.info("\n=== 财联社新闻摘要 ===")
        cls_news = df[df['source'] == '财联社']
        if not cls_news.empty:
            for _, row in cls_news.iterrows():
                self.logger.info(f"[{row['time'].strftime('%Y-%m-%d %H:%M:%S')}] {row['title']}")
                
        self.logger.info("\n=== 万得新闻摘要 ===")
        wind_news = df[df['source'] == '万得']
        if not wind_news.empty:
            for _, row in wind_news.iterrows():
                self.logger.info(f"[{row['time'].strftime('%Y-%m-%d %H:%M:%S')}] [{row.get('type', '普通新闻')}] {row['title']}")
                
        # 打印统计信息
        self.logger.info("\n=== 聚合新闻统计 ===")
        self.logger.info(f"总计获取{len(df)}条新闻")
        self.logger.info(f"新闻来源分布:\n{df['source'].value_counts()}")
        if 'type' in df.columns:
            self.logger.info(f"\n新闻类型分布:\n{df['type'].value_counts()}") 