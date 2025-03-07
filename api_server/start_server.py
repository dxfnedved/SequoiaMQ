"""
启动API服务器

这个脚本用于启动SequoiaMQ的API服务器
"""

import os
import sys
import argparse
import uvicorn
import traceback

def main():
    """主函数"""
    try:
        parser = argparse.ArgumentParser(description="启动API服务器")
        parser.add_argument("--host", type=str, default="0.0.0.0", help="主机地址")
        parser.add_argument("--port", type=int, default=8002, help="端口号")
        parser.add_argument("--reload", action="store_true", help="是否自动重载")
        parser.add_argument("--workers", type=int, default=1, help="工作进程数量 (默认: 1)")
        parser.add_argument("--log-level", type=str, default="info", help="日志级别")
        
        args = parser.parse_args()
        
        # 将项目根目录添加到路径中
        api_server_path = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(api_server_path)
        sys.path.append(project_root)
        
        # 确保日志目录存在
        os.makedirs(os.path.join(project_root, 'logs'), exist_ok=True)
        
        print(f"启动API服务器 host={args.host}, port={args.port}")
        print(f"Python路径: {sys.path}")
        print(f"当前工作目录: {os.getcwd()}")
        
        uvicorn.run(
            "api_server.main:app", 
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers,
            log_level=args.log_level,
            timeout_keep_alive=120  # 增加保持连接超时时间
        )
    except Exception as e:
        print(f"启动API服务器时发生错误: {str(e)}")
        print("详细错误信息:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 