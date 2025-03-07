#!/bin/bash

echo "启动SequoiaMQ服务..."

# 设置环境变量
API_SERVER_DIR="api_server"
FRONTEND_DIR="frontend-vue"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python，请确保Python已安装。"
    exit 1
fi

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "错误: 未找到Node.js，请确保Node.js已安装。"
    exit 1
fi

# 启动后端API服务
echo "正在启动后端API服务..."
cd "$API_SERVER_DIR" || exit
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py &
API_PID=$!
cd ..

# 等待后端服务启动
echo "等待后端服务启动..."
sleep 5

# 启动前端服务
echo "正在启动前端服务..."
cd "$FRONTEND_DIR" || exit
npm install
npm run serve &
FRONTEND_PID=$!
cd ..

echo "服务启动中，请稍候..."
echo "前端服务将在 http://localhost:8080 上运行"
echo "后端API服务将在 http://localhost:5000 上运行"

# 打开浏览器（如果在有GUI的环境中）
sleep 10
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8080
elif command -v open &> /dev/null; then
    open http://localhost:8080
fi

echo "服务已启动完成！"

# 处理终止信号
trap 'echo "正在关闭服务..."; kill $API_PID $FRONTEND_PID; exit' INT TERM

# 保持脚本运行
wait 