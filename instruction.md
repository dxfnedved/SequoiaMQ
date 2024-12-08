# SequoiaMQ 量化交易系统说明文档

## 1. 项目概述

SequoiaMQ 是一个基于 Python 的量化交易分析系统，集成了多种交易策略和技术分析工具，提供图形化界面进行股票分析和策略回测。

### 1.1 核心功能

- 股票数据实时获取和缓存
- 多因子分析策略（Alpha101、Alpha191）
- 技术指标分析（RSRS、海龟交易法则等）
- 图形化股票走势展示
- 自选股管理和批量分析
- 买卖信号实时提示
- 分析结果导出功能

### 1.2 目标和宗旨

- 为投资者提供专业的量化分析工具
- 集成多种成熟的交易策略
- 提供直观的可视化界面
- 支持策略的快速验证和优化
- 保证数据的实时性和准确性

## 2. 技术栈

### 2.1 核心框架和库

- **GUI框架**: PySide6
- **数据处理**: Pandas, NumPy
- **技术分析**: TA-Lib
- **数据可视化**: Matplotlib, mplfinance
- **数据获取**: Akshare
- **日志管理**: Loguru

### 2.2 依赖包版本

```
akshare>=1.15.0
numpy>=1.20.0
pandas>=1.3.0
scikit-learn>=0.24.0
schedule>=1.1.0
TA-Lib>=0.4.0
PyYAML>=5.4.0
requests>=2.26.0
tqdm>=4.65.0
colorama>=0.4.0
PySide6>=6.6.1
shiboken6>=6.6.1
pypinyin>=0.49.0
matplotlib>=3.7.1
mplfinance
plotly>=5.6.0
loguru>=0.7.2
```

## 3. 项目结构

```
SequoiaMQ/
├── strategy/                # 策略模块
│   ├── __init__.py
│   ├── RSRS.py            # RSRS策略
│   ├── alpha_factors101.py # Alpha101因子
│   ├── alpha_factors191.py # Alpha191因子
│   ├── enter.py           # 入场策略
│   └── turtle_trade.py    # 海龟交易策略
├── cache/                  # 数据缓存目录
├── data/                   # 数据存储目录
│   └── watchlist.json     # 自选股列表
├── logs/                   # 日志目录
├── main.py                # 主程序入口
├── main_window.py         # 主窗口
├── stock_chart.py         # 股票图表
├── stock_search.py        # 股票搜索
├── stock_cache.py         # 股票缓存
├── work_flow.py           # 工作流程
├── data_fetcher.py        # 数据获取
├── settings.py            # 配置管理
├── logger_manager.py      # 日志管理
├── analysis_dialog.py     # 分析结果对话框
├── requirements.txt       # 依赖包列表
├── config.yaml           # 配置文件
└── Dockerfile            # Docker配置文件
```

## 4. 数据流设计

### 4.1 数据获取流程

1. 首次启动时从网络获取股票列表
2. 使用本地缓存优化数据加载
3. 按需获取个股详细数据
4. 多线程异步数据获取

### 4.2 数据存储结构

- 股票基础信息（代码、名称、拼音）
- 行情数据（开高低收、成交量）
- 技术指标数据
- 分析结果数据
- 自选股列表（JSON格式）

## 5. 界面设计

### 5.1 配色方案

- 主色调：#1976D2（蓝色）
- 次要色：#FB8C00（橙色）
- 辅助色：#7B1FA2（紫色）
- 成功色：#388E3C（绿色）
- 警告色：#D32F2F（红色）
- 背景色：#FFFFFF（白色）
- 文字色：#333333（深灰）

### 5.2 主要组件

#### 5.2.1 股票搜索组件
- 支持代码、名称、拼音搜索
- 实时过滤显示
- 一键添加自选

#### 5.2.2 自选股列表
- 显示代码和名称
- 双击查看走势图
- 支持批量分析
- 自动保存记录

#### 5.2.3 图表组件
- K线图显示
- 成交量显示
- 均线叠加
- 技术指标
- 买卖点标记

#### 5.2.4 分析结果组件
- 策略分析结果展示
- 数据导出功能（JSON格式）
- 详细信息显示
- 批量分析支持

## 6. 策略系统

### 6.1 内置策略

1. **RSRS策略**
   - 阻力支撑相对强度策略
   - 基于分位数的择时
   - 实时买卖信号

2. **Alpha101策略**
   - 多因子选股
   - 动量、反转、波动等因子
   - 因子组合信号

3. **海龟交易策略**
   - 趋势跟踪
   - 突破信号
   - 仓位管理

4. **技术分析策略**
   - 均线策略
   - 成交量分析
   - 突破策略

### 6.2 策略评估指标

- 年化收益率
- 最大回撤
- 夏普比率
- 胜率统计
- 盈亏比

## 7. 部署说明

### 7.1 环境要求

- Python 3.8+
- 操作系统：Windows/Linux
- 内存：4GB+
- 磁盘空间：10GB+

### 7.2 Docker部署

```bash
# 构建镜像
docker build -t sequoiamq .

# 运行容器
docker run -d \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  --name sequoiamq \
  sequoiamq
```

## 8. 使用说明

### 8.1 启动方式

```bash
# GUI模式
python main.py --gui

# 命令行模式
python main.py
```

### 8.2 配置文件

config.yaml 示例：
```yaml
cron: false
data_dir: "data"
cache_dir: "cache"
log_level: "INFO"
```

### 8.3 自选股管理

1. 在搜索框中输入股票代码或名称
2. 点击搜索结果添加到自选股
3. 自选股会自动保存到 data/watchlist.json
4. 双击自选股查看走势图
5. 使用批量分析功能分析所有自选股

### 8.4 分析结果导出

1. 选择单个或多个股票进行分析
2. 在分析结果对话框中点击"导出JSON"
3. 选择保存位置并确认
4. 结果将以JSON格式保存

## 9. 注意事项

1. 数据源限制
   - 实时数据刷新频率
   - 历史数据获取限制
   - API调用频率限制

2. 系统性能
   - 内存使用优化
   - 数据缓存策略
   - 并发请求控制

3. 错误处理
   - 网络连接错误提示
   - 数据获取失败提示
   - 分析过程异常提示

4. 免责声明
   - 策略仅供参考
   - 投资有风险
   - 数据仅供参考
``` 