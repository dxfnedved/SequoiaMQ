import os
import sys
import subprocess
from colorama import init, Fore, Style

def main():
    """启动器主函数"""
    # 初始化colorama
    init(autoreset=True)
    
    try:
        print(f"{Fore.CYAN}正在启动 SequoiaMQ...{Style.RESET_ALL}")
        
        # 获取当前脚本所在目录
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            base_path = os.path.dirname(sys.executable)
        else:
            # 如果是python脚本
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        # 切换到项目目录
        os.chdir(base_path)
        
        # 检查必要的目录是否存在
        required_dirs = ['logs', 'cache', 'summary']
        for dir_name in required_dirs:
            os.makedirs(dir_name, exist_ok=True)
            
        print(f"{Fore.GREEN}环境检查完成，开始执行主程序...{Style.RESET_ALL}")
        
        # 导入并执行main模块
        import main
        main.main()
        
        # 程序执行完成后等待用户输入
        print(f"\n{Fore.CYAN}程序执行完成，按任意键退出...{Style.RESET_ALL}")
        input()
        
    except Exception as e:
        print(f"{Fore.RED}程序执行出错: {str(e)}{Style.RESET_ALL}")
        print("\n按任意键退出...")
        input()
        sys.exit(1)

if __name__ == '__main__':
    main() 