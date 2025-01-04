import os
import sys
import shutil
import subprocess
import traceback
from colorama import init, Fore, Style

def get_installed_packages():
    """获取已安装的包列表"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True)
        packages = {}
        for line in result.stdout.split('\n')[2:]:  # 跳过头两行
            if line.strip():
                name = line.split()[0].lower()
                packages[name] = True
        return packages
    except Exception as e:
        print(f"{Fore.RED}获取已安装包列表失败: {str(e)}{Style.RESET_ALL}")
        return {}

def main():
    """打包脚本主函数"""
    init(autoreset=True)
    
    try:
        print(f"{Fore.CYAN}开始打包 SequoiaMQ...{Style.RESET_ALL}")
        
        # 检查是否安装了必要的包
        required_packages = {
            'pyinstaller': 'pyinstaller',
            'pandas': 'pandas',
            'numpy': 'numpy',
            'akshare': 'akshare',
            'requests': 'requests',
            'beautifulsoup4': 'bs4',
            'colorama': 'colorama',
            'tqdm': 'tqdm',
            'openai': 'openai',
            'httpx': 'httpx',
            'python-dotenv': 'dotenv'
        }
        
        print(f"{Fore.YELLOW}正在检查依赖包...{Style.RESET_ALL}")
        installed_packages = get_installed_packages()
        missing_packages = []
        
        for package, import_name in required_packages.items():
            if package.lower() not in installed_packages:
                missing_packages.append(package)
                
        if missing_packages:
            print(f"{Fore.RED}缺少以下依赖包：{', '.join(missing_packages)}")
            print(f"请使用以下命令安装：")
            print(f"pip install {' '.join(missing_packages)}{Style.RESET_ALL}")
            return
            
        print(f"{Fore.GREEN}所有依赖包检查通过{Style.RESET_ALL}")
            
        # 清理之前的构建文件
        print(f"{Fore.YELLOW}清理旧的构建文件...{Style.RESET_ALL}")
        build_dirs = ['build', 'dist']
        for dir_name in build_dirs:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                
        # 运行 PyInstaller
        print(f"{Fore.YELLOW}开始构建可执行文件...{Style.RESET_ALL}")
        result = subprocess.run(['pyinstaller', 'sequoiamq.spec'], 
                              capture_output=True, text=True)
                              
        if result.returncode != 0:
            print(f"{Fore.RED}构建失败！错误信息：{Style.RESET_ALL}")
            print(result.stderr)
            return
        
        if os.path.exists(os.path.join('dist', 'SequoiaMQ.exe')):
            print(f"{Fore.GREEN}打包成功！{Style.RESET_ALL}")
            print(f"可执行文件位置：{os.path.abspath(os.path.join('dist', 'SequoiaMQ.exe'))}")
        else:
            print(f"{Fore.RED}打包失败！{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}打包过程出错: {str(e)}{Style.RESET_ALL}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main() 