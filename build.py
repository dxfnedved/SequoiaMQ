import os
import sys
import shutil
import subprocess
import traceback
from colorama import init, Fore, Style
import platform

def check_vs_build_tools():
    """检查Visual Studio Build Tools是否正确安装"""
    try:
        # 检查多个可能的编译器命令
        compilers = ["cl", "nmake", "link"]
        found = False
        for compiler in compilers:
            try:
                result = subprocess.run(
                    [compiler, "/?"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True
                )
                if result.returncode == 0:
                    found = True
                    break
            except:
                continue

        if not found:
            print(f"{Fore.RED}未找到Visual Studio Build Tools。")
            print("请确保以下步骤已完成：")
            print("1. 安装Visual Studio Build Tools")
            print("2. 在系统环境变量中添加Visual Studio Build Tools的路径")
            print("3. 使用'Developer Command Prompt for VS'运行此脚本")
            print("或者直接从开始菜单运行'x64 Native Tools Command Prompt for VS'后再执行此脚本")
            print(f"下载链接：https://visualstudio.microsoft.com/visual-cpp-build-tools/{Style.RESET_ALL}")
            return False

        return True

    except Exception as e:
        print(f"{Fore.RED}检查Visual Studio Build Tools时出错: {str(e)}{Style.RESET_ALL}")
        return False

def run_nuitka():
    """运行Nuitka打包"""
    try:
        # 构建Nuitka命令
        cmd = [
            sys.executable,
            "-m",
            "nuitka",
            "--standalone",  # 生成独立可执行文件
            "--follow-imports",  # 自动包含所有导入
            "--enable-plugin=data-files",  # 启用数据文件插件
            "--include-package=akshare",  # 包含akshare包
            "--include-package=bs4",  # 包含bs4包
            "--include-package=httpx",  # 包含httpx包
            "--include-package=colorama",  # 包含colorama包
            "--include-package=tqdm",  # 包含tqdm包
            "--include-package=dotenv",  # 包含python-dotenv包
            "--include-package=sklearn",  # 包含scikit-learn包
            "--include-package=schedule",  # 包含schedule包
            "--include-package=talib",  # 包含TA-Lib包
            "--include-package=yaml",  # 包含PyYAML包
            "--include-package=loguru",  # 包含loguru包
            "--include-package=chinese_calendar",  # 包含chinese-calendar包
            "--include-package=pandas",  # 包含pandas包
            "--include-data-dir=strategy=strategy",  # 包含strategy目录
            "--include-data-file=main.py=main.py",  # 包含主程序
            "--include-data-file=settings.py=settings.py",  # 包含设置文件
            "--include-data-file=work_flow.py=work_flow.py",  # 包含工作流文件
            "--include-data-file=data_fetcher.py=data_fetcher.py",  # 包含数据获取文件
            "--include-data-file=stock_cache.py=stock_cache.py",  # 包含缓存文件
            "--include-data-file=utils.py=utils.py",  # 包含工具文件
            "--include-data-file=logger_manager.py=logger_manager.py",  # 包含日志管理文件
            "--include-data-file=.env=.env",  # 包含环境变量文件
            "--include-data-file=README.md=README.md",  # 包含说明文件
            "--windows-company-name=SequoiaMQ",  # 设置公司名
            "--windows-product-name=SequoiaMQ",  # 设置产品名
            "--windows-file-version=1.0.0",  # 设置文件版本
            "--windows-product-version=1.0.0",  # 设置产品版本
            "--output-dir=dist",  # 输出目录
            "--remove-output",  # 清理之前的输出
            "--show-progress",  # 显示进度
            "--show-memory",  # 显示内存使用
            "--jobs=4",  # 使用4个线程编译
            "--nofollow-import-to=tkinter",  # 排除tkinter
            "--nofollow-import-to=PyQt5",  # 排除PyQt5
            "--nofollow-import-to=PyQt6",  # 排除PyQt6
            "--nofollow-import-to=streamlit",  # 排除streamlit
            "--nofollow-import-to=news_sources",  # 排除news_sources
            "--nofollow-import-to=matplotlib",  # 排除matplotlib
            "--nofollow-import-to=plotly",  # 排除plotly
            "--nofollow-import-to=stock_selector",  # 排除stock_selector
            "--warn-unusual-code",  # 显示异常代码警告
            "--assume-yes-for-downloads",  # 自动下载依赖
            "main.py"  # 主程序入口
        ]

        # 移除空选项
        cmd = [x for x in cmd if x]

        print(f"{Fore.YELLOW}开始打包...{Style.RESET_ALL}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )

        # 实时显示输出
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                print(output.strip())

        # 获取错误输出
        _, stderr = process.communicate()
        if stderr:
            print(f"{Fore.RED}错误输出：{Style.RESET_ALL}")
            print(stderr)

        return process.returncode == 0

    except Exception as e:
        print(f"{Fore.RED}执行Nuitka打包失败: {str(e)}{Style.RESET_ALL}")
        return False

def main():
    """打包脚本主函数"""
    init(autoreset=True)

    try:
        print(f"{Fore.CYAN}开始打包 SequoiaMQ...{Style.RESET_ALL}")

        # 检查系统要求
        if platform.system() == "Windows":
            print(f"{Fore.YELLOW}检查系统要求...{Style.RESET_ALL}")
            if not check_vs_build_tools():
                return

        # 清理之前的构建文件
        print(f"{Fore.YELLOW}清理旧的构建文件...{Style.RESET_ALL}")
        build_dirs = ["build", "dist", "launcher.build", "launcher.dist"]
        for dir_name in build_dirs:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)

        # 运行Nuitka打包
        print(f"{Fore.YELLOW}开始构建可执行文件...{Style.RESET_ALL}")
        if run_nuitka():
            exe_name = "launcher.exe" if platform.system() == "Windows" else "launcher"
            if os.path.exists(os.path.join("dist", exe_name)):
                # 重命名可执行文件
                os.rename(
                    os.path.join("dist", exe_name),
                    os.path.join("dist", "SequoiaMQ.exe" if platform.system() == "Windows" else "SequoiaMQ")
                )
                print(f"{Fore.GREEN}打包成功！{Style.RESET_ALL}")
                print(
                    f"可执行文件位置：{os.path.abspath(os.path.join('dist', 'SequoiaMQ.exe' if platform.system() == 'Windows' else 'SequoiaMQ'))}"
                )
            else:
                print(f"{Fore.RED}打包失败！未找到生成的可执行文件{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}打包失败！{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}打包过程出错: {str(e)}{Style.RESET_ALL}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 