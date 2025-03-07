@echo off
echo 启动SequoiaMQ服务...

:: 设置环境变量
set API_SERVER_DIR=api_server
set FRONTEND_DIR=frontend-vue

:: 检查Python环境
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误: 未找到Python，请确保Python已安装并添加到PATH中。
    exit /b 1
)

:: 检查Node.js环境
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误: 未找到Node.js，请确保Node.js已安装并添加到PATH中。
    exit /b 1
)

:: 启动后端API服务
echo 正在启动后端API服务...
start cmd /k "cd %API_SERVER_DIR% && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python main.py"

:: 等待后端服务启动
echo 等待后端服务启动...
timeout /t 5 /nobreak

:: 启动前端服务
echo 正在启动前端服务...
start cmd /k "cd %FRONTEND_DIR% && npm install && npm run serve"

echo 服务启动中，请稍候...
echo 前端服务将在 http://localhost:8080 上运行
echo 后端API服务将在 http://localhost:5000 上运行

:: 打开浏览器
timeout /t 10 /nobreak
start http://localhost:8080

echo 服务已启动完成！ 