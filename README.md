# SequoiaMQ - 智能股票分析与预测系统

SequoiaMQ是一个基于Python和Vue.js的智能股票分析与预测系统，集成了LSTM深度学习模型和大型语言模型(LLM)，为用户提供全面的股票市场分析和预测服务。

## 主要功能

- **股票搜索与自选股管理**：快速搜索股票，管理自选股列表
- **LSTM预测**：基于深度学习的股票价格预测
- **LLM大模型分析**：利用大型语言模型进行股票基本面和技术面分析
- **多策略组合分析**：结合多种交易策略进行综合分析
- **响应式设计**：支持在桌面和移动设备上使用

## 技术栈

### 后端
- Python 3.9+
- Flask (API服务)
- SQLAlchemy (数据库ORM)
- PyTorch (深度学习)
- pandas, numpy (数据处理)
- tushare, akshare (金融数据API)

### 前端
- Vue 3
- Element Plus (UI组件库)
- ECharts (图表可视化)
- Axios (HTTP客户端)
- Vite (构建工具)

## 安装与运行

### 方法一：直接运行

#### 前提条件
- Python 3.9+
- Node.js 16+
- npm 7+

#### 步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/SequoiaMQ.git
cd SequoiaMQ
```

2. 使用启动脚本

**Windows:**
```
start-services.bat
```

**Linux/macOS:**
```bash
chmod +x start-services.sh
./start-services.sh
```

### 方法二：Docker部署

#### 前提条件
- Docker
- Docker Compose

#### 步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/SequoiaMQ.git
cd SequoiaMQ
```

2. 使用Docker部署脚本

**Windows:**
```
deploy-docker.bat
```

**Linux/macOS:**
```bash
chmod +x deploy-docker.sh
./deploy-docker.sh
```

## 使用指南

1. **股票搜索**：在搜索框中输入股票代码或名称，系统会自动显示匹配结果
2. **LSTM预测**：选择股票后，设置预测参数，点击"开始预测"按钮
3. **LLM分析**：选择股票和LLM模型，点击"开始分析"按钮
4. **多策略分析**：选择策略组合和股票，设置分析参数，点击"运行分析"按钮
5. **自选股管理**：在自选股页面添加、删除和管理您的自选股列表

## 项目结构

```
SequoiaMQ/
├── api_server/            # 后端API服务
├── frontend-vue/          # 前端Vue应用
├── data/                  # 数据目录
├── logs/                  # 日志目录
├── docker-compose.yml     # Docker Compose配置
├── start-services.bat     # Windows启动脚本
├── start-services.sh      # Linux启动脚本
├── deploy-docker.bat      # Windows Docker部署脚本
└── deploy-docker.sh       # Linux Docker部署脚本
```

## 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## Sequoia选股系统
### 简介
本程序使用[AKShare接口](https://github.com/akfamily/akshare)，从东方财富获取数据。

本程序实现了若干种选股策略，大家可以自行选择其中的一到多种策略组合使用，参见[work_flow.py](https://github.com/sngyai/Sequoia/blob/master/work_flow.py#L28-L38)，也可以实现自己的策略。

各策略中的`end_date`参数主要用于回测。

### 系统优化
最新版本对策略分析系统进行了全面优化，主要包括：

1. **并行策略执行**：
   - 高优先级策略串行执行，低优先级策略并行执行
   - 基于线程池的批处理机制
   - 可配置的并行度和批处理大小

2. **缓存机制**：
   - 策略结果缓存，避免重复计算
   - 技术指标缓存，提高计算效率
   - 智能缓存失效机制

3. **性能监控**：
   - 详细的执行时间统计
   - 策略执行效率分析
   - 缓存命中率监控

4. **数据预处理优化**：
   - 自动填充缺失值
   - 预计算常用技术指标
   - 数据验证和清洗

5. **策略优先级**：
   - 基于重要性的策略执行顺序
   - 关键策略优先执行
   - 资源分配优化

## 准备工作:
###  环境&依赖管理
推荐使用 Miniconda来进行 Python 环境管理 [Miniconda — conda documentation](https://docs.conda.io/en/latest/miniconda.html)

安装 conda 后，切换到项目专属环境进行配置，例如：
```
conda create -n sequoia39 python=3.9
conda activate sequoia39
```

 ### 根据不同的平台安装TA-Lib程序

* Mac OS X  (x86_64)

    ```  
    $ brew install ta-lib    
    # conda 环境下 可直接执行
    $ conda install -c conda-forge ta-lib
    ``` 

* Mac OS X (arm64)

    需要特殊说明的是
    M1 芯片的 Mac OS 很多库和依赖都需要基于 arm64 来构建。
    所以，这里首先需要确认安装的 homebrew 是 arm 版本，如果之前安装的 homebrew 是 x86 版本，推荐重装 homebrew。
  1. 删除老版本 homebrew （如果之前安装的是 x86版本 homebrew，重装前需要删除）
    ```
      sudo rm -rf /usr/local/.git
      rm -rf ~/Library/Caches/Homebrew
      rm -rf /usr/local/Homebrew 
    ```

  2. 安装/重装 arm64 版本 homebrew
    ```
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ```

   3. homebrew 初始化
    ```
    vim ~/.zshrc
    
    # 加入到系统环境变量
    export PATH=/opt/homebrew/bin:$PATH
    
    source ~/.zshrc
    # 确认版本信息
    brew config 
    ```
  4. 过程中遇到问题的参考解决办法
  - [macos - zsh problem: compinit:503: no such file or directory: /usr/local/share/zsh/site-functions/_brew - Stack Overflow](https://stackoverflow.com/questions/65747286/zsh-problem-compinit503-no-such-file-or-directory-usr-local-share-zsh-site)
  - [The required file "libmini_racer.dylib" can't be found in mac M1 · Issue #143 · sqreen/PyMiniRacer](https://github.com/sqreen/PyMiniRacer/issues/143)
  - [Installing python tables on mac with m1 chip - Stack Overflow](https://stackoverflow.com/questions/65839750/installing-python-tables-on-mac-with-m1-chip)

  5. 经过以上步骤后，可以开始继续安装 `ta-lib` 了。 参考
  - [TA-Lib · PyPI](https://pypi.org/project/TA-Lib/)
  - [说说 talib(ta-lib) 这个技术指标库，各系统怎么最轻松安装 ta-lib - 知乎](https://zhuanlan.zhihu.com/p/546720500)

  以下是完整的操作命令示例：

    ```
    # 操作示例
    # 1. 创建专属 python 环境
    conda create -n sequoia39 python=3.9
    conda activate sequoia39
    
    # 2. 安装 ta-lib 库
    arch -arm64 brew install ta-lib
    export TA_INCLUDE_PATH="$(brew --prefix ta-lib)/include"
    export TA_LIBRARY_PATH="$(brew --prefix ta-lib)/lib"
    python3.9 -m pip install --no-cache-dir ta-lib
    
    # 3. 验证是否安装成功
    python -c "import talib; print(talib.__version__)"
    ```

* Windows

    下载 [ta-lib-0.4.0-msvc.zip](http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-msvc.zip)，解压到 ``C:\ta-lib``



* Linux

    下载 [ta-lib-0.4.0-src.tar.gz](http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz) :
    ```
    $ untar and cd
    $ ./configure --prefix=/usr
    $ make
    $ sudo make install
    ```
 ### 推荐使用Python3.8以上以及pip3
 ### Python 依赖:
 ```
 pip install -r requirements.txt 
 ```
 ### 更新akshare数据接口
 本项目已切换至akshare数据接口，该项目更新频率较高，使用前建议检查接口更新
``` 
pip install akshare --upgrade
```
 ### 生成配置文件

```
cp config.yaml.example config.yaml
```
## 运行
### 本地运行
```
$ python main.py
```
运行结果查看 logs 目录下生成的日志文件 格式为 `logs/sequoia-$YEAR-$MONTH-$DAY-$HOUR-$MINUTE-$SECOND.log`
如：`logs/sequoia-2023-03-03-20-47-56.log`

### 服务器端运行
#### 定时任务
服务器端运行需要改为定时任务，共有两种方式：
1. 使用Python schedule定时任务
   * 将[config.yaml](config.yaml.example)中的`cron`配置改为`true`，`push`.`enable`改为`true`

2. 使用crontab定时任务
   * 保持[config.yaml](config.yaml.example)中的`cron`配置为***false***，`push`.`enable`为`true`
   * [安装crontab](https://www.digitalocean.com/community/tutorials/how-to-use-cron-to-automate-tasks-ubuntu-1804)
   * `crontab -e` 添加如下内容(服务器端安装了miniconda3)：
   ```bash
    SHELL=/bin/bash
    PATH=/usr/bin:/bin:/home/ubuntu/miniconda3/bin/
    # m h  dom mon dow   command
    0 3 * * 1-5 source /home/ubuntu/miniconda3/bin/activate python3.10; python3 /home/ubuntu/Sequoia/main.py >> /home/ubuntu/Sequoia/sequoia.log; source /home/ubuntu/miniconda3/bin/deactivate
   ```
#### 微信推送
使用[WxPusher](https://wxpusher.zjiecode.com/docs/#/)实现了微信推送，用户需要自行获取[wxpusher_token](https://wxpusher.zjiecode.com/docs/#/?id=%e8%8e%b7%e5%8f%96apptoken)和[wxpusher_uid](https://wxpusher.zjiecode.com/docs/#/?id=%e8%8e%b7%e5%8f%96uid)，并配置到`config.yaml`中去。


## 如何回测
修改[config.yaml](config.yaml.example)中`end_date`为指定日期，格式为`'YYYY-MM-DD'`，如：
```
end = '2019-06-17'
```

## 性能优化指南

### 1. 调整并行度
可以通过修改`work_flow.py`中的`max_workers`参数来调整并行度：
```python
# 性能优化参数
self.max_workers = min(64, (os.cpu_count() or 1) * 8)  # 线程数
```

### 2. 批处理大小
批处理大小影响内存使用和处理效率，可以根据系统资源调整：
```python
self.batch_size = 200  # 批处理大小
```

### 3. 缓存配置
可以调整缓存有效期来平衡性能和数据实时性：
```python
self.cache_duration = 24 * 60 * 60  # 24小时，单位：秒
```

### 4. 策略优先级
可以在`strategy_analyzer.py`中调整策略优先级：
```python
self.strategy_priorities = {
    'RSRS_Strategy': 1,  # 数字越小优先级越高
    'TurtleStrategy': 2,
    # ...
}
```

