#!/bin/bash

echo "开始部署SequoiaMQ Docker服务..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: 未找到Docker，请确保Docker已安装。"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: 未找到Docker Compose，请确保Docker Compose已安装。"
    exit 1
fi

# 创建必要的目录
mkdir -p data logs

# 停止并移除现有容器
echo "停止并移除现有容器..."
docker-compose down

# 构建新镜像
echo "构建Docker镜像..."
docker-compose build

# 启动容器
echo "启动Docker容器..."
docker-compose up -d

# 检查容器状态
echo "检查容器状态..."
docker-compose ps

echo "部署完成！"
echo "前端服务运行在: http://localhost:8080"
echo "后端API服务运行在: http://localhost:5000"

# 打开浏览器（如果在有GUI的环境中）
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8080
elif command -v open &> /dev/null; then
    open http://localhost:8080
fi 