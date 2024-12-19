import os
import json
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
from strategy.base import BaseStrategy
import akshare as ak
from openai import OpenAI
import time

class NewsStrategy(BaseStrategy):
    """新闻舆情策略 - 全局分析版本"""
    def __init__(self, logger_manager=None):
        super().__init__(logger_manager)
        self.name = "NewsStrategy"
        load_dotenv()  # 加载环境变量
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=os.getenv('LLM_API_KEY'),
            base_url=os.getenv('LLM_API_ENDPOINT')
        )
        
        # 新闻分析参数
        self.news_days = 2  # 分析最近2天的新闻
        self.min_relevance = 0.6  # 最小相关度阈值
        
        # 缓存全局分析结果
        self.global_analysis = None
        self.last_analysis_time = None
        self.analysis_cache_duration = 4 * 60 * 60  # 4小时更新一次
        
    def get_news(self):
        """获取新闻数据"""
        try:
            # 计算时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.news_days)
            
            try:
                # 获取东方财富新闻
                news_df = ak.stock_news_em()
                if news_df is None or news_df.empty:
                    self.logger.warning("未获取到东方财富新闻数据")
                    return None
                    
                # 确保必要的列存在
                required_columns = ['时间', '标题', '内容']
                if not all(col in news_df.columns for col in required_columns):
                    self.logger.error("新闻数据缺少必要的列")
                    return None
                    
                # 重命名列
                news_df = news_df.rename(columns={
                    '时间': 'datetime',
                    '标题': 'title',
                    '内容': 'content'
                })
                
                # 转换datetime列
                news_df['datetime'] = pd.to_datetime(news_df['datetime'], format='%Y-%m-%d %H:%M:%S')
                
                # 删除无效的datetime记录
                news_df = news_df.dropna(subset=['datetime'])
                
                # 过滤时间范围
                news_df = news_df[
                    (news_df['datetime'] >= start_date) &
                    (news_df['datetime'] <= end_date)
                ]
                
                if news_df.empty:
                    self.logger.warning("过滤后没有符合时间范围的新闻")
                    return None
                    
                return news_df
                
            except Exception as e:
                self.logger.error(f"获取东方财富新闻数据失败: {str(e)}")
                return None
            
        except Exception as e:
            self.logger.error(f"获取新闻数据失败: {str(e)}")
            return None
            
    def analyze_news_sentiment(self, news_list):
        """使用OpenAI分析新闻情感"""
        try:
            # 限制新闻数量，避免token超限
            max_news = 20
            if len(news_list) > max_news:
                self.logger.info(f"新闻数量过多，将只分析最新的{max_news}条新闻")
                news_list = sorted(news_list, key=lambda x: x['datetime'], reverse=True)[:max_news]
            
            # 格式化新闻列表，只包含必要信息
            formatted_news = []
            for news in news_list:
                formatted_news.append({
                    'datetime': news['datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                    'title': news['title'],
                    'content': news['content'][:500] if len(news['content']) > 500 else news['content']  # 限制内容长度
                })
            
            # 构建提示词，使用CoT方法
            prompt = f"""请分析以下{len(formatted_news)}条新闻对A股市场的影响。让我们一步步思考：

1. 首先，让我们分类这些新闻：
   - 宏观经济新闻
   - 行业政策新闻
   - 公司新闻

2. 然后，评估每类新闻的影响：
   - 对整体市场的影响
   - 对特定行业的影响
   - 对个股的影响
   - 影响的持续时间

3. 接着，分析情绪因素：
   - 市场情绪（乐观/悲观）
   - 政策导向（利好/利空）
   - 资金面（宽松/紧张）

4. 最后，得出结论：
   - 市场整体趋势判断
   - 重点关注的行业
   - 具体投资建议

新闻内容：
{json.dumps(formatted_news, ensure_ascii=False, indent=2)}

请以JSON格式返回分析结果，包含以下字段：
{
    "market_sentiment": "整体市场情绪",
    "policy_impact": "政策影响分析",
    "capital_flow": "资金面分析",
    "sector_analysis": [
        {
            "sector": "行业名称",
            "impact": "影响程度",
            "recommendation": "投资建议"
        }
    ],
    "stock_picks": [
        {
            "code": "股票代码",
            "name": "股票名称",
            "reason": "推荐理由",
            "signal": "买入/卖出/观望"
        }
    ],
    "risk_factors": ["风险因素列表"],
    "confidence_score": "分析置信度(0-1)",
    "analysis_summary": "详细分析总结"
}"""
            
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的金融分析师，擅长分析新闻对A股市场的影响。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # 解析返回结果
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            self.logger.error(f"分析新闻情感失败: {str(e)}")
            return None
            
    def perform_global_analysis(self):
        """执行全局新闻分析"""
        try:
            # 检查是否需要更新分析
            current_time = datetime.now()
            if (self.global_analysis is not None and 
                self.last_analysis_time is not None and
                (current_time - self.last_analysis_time).total_seconds() < self.analysis_cache_duration):
                return self.global_analysis
                
            # 获取新闻数据
            news_df = self.get_news()
            if news_df is None or news_df.empty:
                self.logger.warning("未获取到有效的新闻数据，跳过新闻分析")
                return None
                
            # 准备新闻列表
            news_list = news_df[['datetime', 'title', 'content']].to_dict('records')
            
            # 分析新闻情感
            analysis_result = self.analyze_news_sentiment(news_list)
            if analysis_result is None:
                self.logger.warning("新闻情感分析失败，跳过新闻分析")
                return None
                
            # 更新缓存
            self.global_analysis = analysis_result
            self.last_analysis_time = current_time
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"执行全局新闻分析失败: {str(e)}")
            return None
            
    def analyze(self, data):
        """分析数据并生成交易信号"""
        try:
            if not self._validate_data(data):
                return None
                
            # 获取股票代码
            code = data.name if hasattr(data, 'name') else None
            if code is None:
                return None
                
            # 获取全局分析结果
            global_result = self.perform_global_analysis()
            if global_result is None:
                return None
                
            # 查找该股票的具体信号
            stock_signal = None
            for stock in global_result.get('stock_picks', []):
                if stock['code'] == code:
                    stock_signal = stock
                    break
                    
            # 生成信号
            signal = "无"
            if stock_signal:
                signal = stock_signal['signal']
                
            return {
                'signal': signal,
                'market_sentiment': global_result['market_sentiment'],
                'sector_analysis': global_result['sector_analysis'],
                'confidence_score': global_result['confidence_score'],
                'analysis_summary': global_result['analysis_summary'],
                'stock_specific': stock_signal
            }
            
        except Exception as e:
            self.logger.error(f"新闻策略分析失败: {str(e)}")
            return None
            
    def get_signals(self, data):
        """获取交易信号"""
        try:
            signals = []
            result = self.analyze(data)
            
            if result and result['signal'] != "无":
                signals.append({
                    'date': data.index[-1],
                    'type': result['signal'],
                    'strategy': self.name,
                    'price': data['close'].iloc[-1],
                    'market_sentiment': result['market_sentiment'],
                    'confidence_score': result['confidence_score'],
                    'analysis_summary': result['analysis_summary'],
                    'stock_specific': result.get('stock_specific', {})
                })
                
            return signals
            
        except Exception as e:
            self.logger.error(f"获取新闻策略信号失败: {str(e)}")
            return []
