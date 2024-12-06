FROM python:3.8-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    make \
    qt6-base-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p /app/data /app/logs

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 设置Python环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=offscreen

# 设置默认命令
ENTRYPOINT ["python", "main.py"]
# 可以通过传递 --gui 参数启动GUI模式
CMD [] 