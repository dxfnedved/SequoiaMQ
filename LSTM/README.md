# LSTM股票预测工具

这是一个基于LSTM和思维增强LSTM的股票价格预测工具，支持通过股票代码或股票名称进行预测。

## 功能特点

- 支持通过股票代码或股票名称进行预测
- 支持批量预测多只股票，并行处理提高效率
- 自动获取股票历史数据和计算技术指标
- 支持标准LSTM和思维增强LSTM两种模型
- 思维增强LSTM模型集成了多头注意力机制和残差连接
- 可预测未来多天的股价走势
- 提供详细的模型评估指标
- 生成预测结果图表和JSON格式的分析报告

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python predict.py 000001  # 使用股票代码
```

或者

```bash
python predict.py 平安银行  # 使用股票名称
```

### 批量预测

```bash
python batch_predict.py 000001 600519 601318  # 批量预测多只股票
```

### 高级选项

```bash
python predict.py 000001 --model_type lstm_with_thoughts --epochs 30 --time_step 50 --future_days 10 --num_heads 8
```

```bash
python batch_predict.py 000001 600519 601318 --model_type lstm_with_thoughts --max_workers 8 --output_dir custom_results
```

### 完整参数说明

#### 单只股票预测 (predict.py)

- `stock`: 股票代码或名称（如：000001或平安银行）
- `--start_date`: 开始日期（格式：YYYYMMDD）
- `--end_date`: 结束日期（格式：YYYYMMDD）
- `--time_step`: 时间步长（默认：60）
- `--epochs`: 训练轮数（默认：20）
- `--batch_size`: 批次大小（默认：32）
- `--future_days`: 预测未来天数（默认：7）
- `--no_plot`: 不显示预测结果图表
- `--model_type`: 模型类型，可选 lstm 或 lstm_with_thoughts（默认：lstm_with_thoughts）
- `--thought_dim`: 思维维度（默认：32）
- `--num_thoughts`: 思维数量（默认：5）
- `--num_heads`: 多头注意力头数（默认：4）

#### 批量预测 (batch_predict.py)

- `stocks`: 股票代码或名称列表（如：000001 600519 601318）
- `--max_workers`: 最大并行工作线程数（默认：4）
- `--output_dir`: 输出目录（默认：results）
- 其他参数与单只股票预测相同

## 模型说明

### 思维增强LSTM模型

思维增强LSTM模型是对传统LSTM的扩展，引入了"思维"机制来提高预测能力。主要特点包括：

1. **多层次思维生成**：为输入序列的每个时间步生成抽象表征
2. **多头注意力机制**：更精细地关注不同时间步的重要性
3. **短期和长期思维**：分别捕捉短期波动和长期趋势
4. **残差连接**：帮助梯度流动和信息传递
5. **层归一化**：提高训练稳定性

### 模型架构

```
输入序列 → LSTM编码器 → 多头注意力 → 思维生成 → 思维组合 → 预测输出
```

## 输出说明

程序会输出以下内容：

1. 模型评估指标：MSE、RMSE、MAE、MAPE
2. 未来价格预测结果
3. 预测结果图表（保存在plots目录）
4. JSON格式的分析报告（保存在results目录）
5. 批量预测时会生成汇总报告（summary_*.json）

## 示例

预测平安银行未来7天的股价：

```bash
python predict.py 平安银行 --future_days 7
```

使用思维增强LSTM模型预测贵州茅台未来10天的股价：

```bash
python predict.py 贵州茅台 --model_type lstm_with_thoughts --future_days 10 --num_heads 8 --thought_dim 64
```

批量预测多只股票：

```bash
python batch_predict.py 000001 600519 601318 --future_days 10 --model_type lstm_with_thoughts
```

## 注意事项

- 股票预测结果仅供参考，不构成投资建议
- 首次运行时需要下载股票数据，可能需要一些时间
- 如果遇到网络问题，可能需要多次尝试
- 批量预测时，建议根据CPU核心数调整max_workers参数


使用股票代码

```bash
python predict.py 000001
```

使用股票名称

```bash
python predict.py 平安银行
```

使用思维增强LSTM模型

```bash
python predict.py 平安银行 --model_type lstm_with_thoughts --num_heads 8
```

使用标准LSTM模型

```bash
python predict.py 贵州茅台 --model_type lstm
```

预测未来10天的股价

```bash
python predict.py 平安银行 --future_days 10
```

不显示图表

```bash
python predict.py 平安银行 --no_plot
```

批量预测多只股票

```bash
python batch_predict.py 000001 600519 601318 --max_workers 8
```

## 项目结构

```
LSTM/
├── main.py                # 主程序入口
├── predict.py             # 预测脚本
├── batch_predict.py       # 批量预测脚本
├── model.py               # 标准LSTM模型实现
├── lstm_with_thoughts.py  # 思维增强LSTM模型实现
├── data_loader.py         # 数据加载模块
├── technical_analyzer.py  # 技术分析指标计算
├── requirements.txt       # 依赖包列表
├── plots/                 # 预测图表输出目录
└── results/               # 分析结果输出目录
```

## 开发计划

- [x] 添加多头注意力机制
- [x] 添加残差连接和层归一化
- [x] 支持批量股票分析
- [ ] 添加模型持久化功能
- [ ] 添加更多可视化选项
- [ ] 实现Web界面

## 免责声明

本工具仅供学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎。作者对使用本工具进行投资决策所产生的任何损失不承担责任。
