# SequoiaMQ 开发指南

## 开发环境设置

### 前提条件

- Python 3.8+
- Node.js 16+
- npm 8+

### 安装依赖

1. 后端依赖:

```bash
# 安装主项目依赖
pip install -r requirements.txt

# 安装API服务器依赖
pip install -r api_server/requirements.txt
```

2. 前端依赖:

```bash
cd frontend-vue
npm install
```

## 数据库配置

项目使用SQLite数据库存储持久化数据，数据库文件将自动创建在 `data/sequoiamq.db` 路径下。

已有的JSON数据将在首次启动时自动迁移到SQLite数据库中。

## 启动项目

### 一键启动前后端服务

使用项目根目录下的 `start.py` 脚本可以同时启动前后端服务：

```bash
python start.py
```

这将同时启动:
- API服务器: http://localhost:8000
- 前端开发服务器: http://localhost:8080

### 仅启动API服务器

```bash
python start.py --api-only
```

### 仅启动前端开发服务器

```bash
python start.py --frontend-only
```

### 手动启动

如果需要分别启动服务，可以:

1. 启动API服务器:

```bash
python -m api_server.start_server
```

2. 启动前端开发服务器:

```bash
cd frontend-vue
npm run serve
```

## 访问应用

前端页面: http://localhost:8080

API文档: http://localhost:8000/docs

## 开发建议

1. 使用一键启动脚本可以同时查看前后端的日志输出
2. API更改后可以直接访问API文档页面查看
3. 前端修改会自动热更新
4. 后端代码修改在开发模式下会自动重新加载 