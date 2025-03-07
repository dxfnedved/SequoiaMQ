import argparse
from workflow_manager import WorkflowManager
from loguru import logger

def main():
    """主函数"""
    try:
        # 创建参数解析器
        parser = argparse.ArgumentParser(description='股票分析工具')
        subparsers = parser.add_subparsers(dest='command', help='可用命令')
        
        # 添加analyze命令
        analyze_parser = subparsers.add_parser('analyze', help='分析股票')
        analyze_parser.add_argument('-s', '--stock', type=str, required=True, help='股票代码或股票简称')
        
        # 解析参数
        args = parser.parse_args()
        
        if args.command == 'analyze':
            # 初始化工作流管理器
            workflow = WorkflowManager()
            
            # 执行股票分析
            if not workflow.analyze_stock(args.stock):
                print("分析失败")
                return
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        print("分析失败")

if __name__ == '__main__':
    main() 