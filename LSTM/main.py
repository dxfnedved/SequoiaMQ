import argparse
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_loader import StockDataLoader
from model import StockLSTM
from lstm_with_thoughts import StockLSTMWithThoughts
from logger_manager import LoggerManager

def save_results(stock_code, metrics, predictions, output_dir='results'):
    """保存分析结果"""
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 准备结果数据
        result = {
            'stock_code': stock_code,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': metrics
        }
        
        # 生成输出文件名
        result_file = os.path.join(output_dir, f"{stock_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # 保存结果
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
            
        print(f"\n分析结果已保存到: {result_file}")
        return result_file
    except Exception as e:
        print(f"保存结果时出错: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='A股LSTM股价预测分析工具')
    parser.add_argument('stock_code', type=str, help='股票代码（如：000001）')
    parser.add_argument('--start_date', type=str, help='开始日期（格式：YYYYMMDD）', default=None)
    parser.add_argument('--end_date', type=str, help='结束日期（格式：YYYYMMDD）', default=None)
    parser.add_argument('--time_step', type=int, help='时间步长（默认：100）', default=100)
    parser.add_argument('--epochs', type=int, help='训练轮数（默认：10）', default=10)
    parser.add_argument('--batch_size', type=int, help='批次大小（默认：32）', default=32)
    parser.add_argument('--no_plot', action='store_true', help='不显示预测结果图表')
    parser.add_argument('--model_type', type=str, choices=['lstm', 'lstm_with_thoughts'], 
                        default='lstm', help='模型类型：lstm或lstm_with_thoughts')
    parser.add_argument('--thought_dim', type=int, default=32, help='思维维度（默认：32）')
    parser.add_argument('--num_thoughts', type=int, default=5, help='思维数量（默认：5）')
    
    args = parser.parse_args()
    
    # 初始化日志管理器
    logger_manager = LoggerManager()
    logger = logger_manager.get_logger("main")
    
    # 初始化数据加载器
    data_loader = StockDataLoader(logger_manager=logger_manager)
    
    try:
        # 格式化并验证股票代码
        stock_code = data_loader.format_stock_code(args.stock_code)
        if not data_loader.validate_stock_code(stock_code):
            logger.error(f"无效的股票代码: {stock_code}")
            sys.exit(1)
        
        # 获取股票名称
        stock_name = data_loader.get_stock_name(stock_code)
        logger.info(f"开始分析 {stock_code}（{stock_name}）的股价数据...")
        
        # 获取股票数据
        df = data_loader.get_stock_data(stock_code, args.start_date, args.end_date)
        if df is None or len(df) == 0:
            logger.error("无法获取股票数据")
            sys.exit(1)
        
        logger.info(f"获取到 {len(df)} 条历史数据")
        
        # 特征列
        feature_columns = ['close', 'ma5', 'ma10', 'ma20', 'price_change', 'volatility']
        
        # 根据选择的模型类型初始化模型
        if args.model_type == 'lstm':
            logger.info("使用标准LSTM模型")
            model = StockLSTM(time_step=args.time_step)
        else:
            logger.info("使用思维增强LSTM模型")
            model = StockLSTMWithThoughts(
                time_step=args.time_step,
                thought_dim=args.thought_dim,
                num_thoughts=args.num_thoughts
            )
        
        # 准备数据
        X_train, Y_train, X_test, Y_test = model.prepare_data(df[feature_columns].values)
        
        # 训练模型
        logger.info("开始训练模型...")
        model.train(X_train, Y_train, epochs=args.epochs, batch_size=args.batch_size)
        
        # 进行预测
        logger.info("生成预测结果...")
        train_predict = model.predict(X_train)
        test_predict = model.predict(X_test)
        
        # 评估模型
        metrics = model.evaluate(X_test, Y_test)
        logger.info("模型评估指标：")
        logger.info(f"均方误差 (MSE): {metrics['MSE']:.4f}")
        logger.info(f"均方根误差 (RMSE): {metrics['RMSE']:.4f}")
        logger.info(f"平均绝对误差 (MAE): {metrics['MAE']:.4f}")
        logger.info(f"平均绝对百分比误差 (MAPE): {metrics['MAPE']:.4f}%")
        
        # 保存结果
        save_results(stock_code, metrics, None)
        
        # 显示预测图表
        if not args.no_plot:
            model.plot_predictions(df['close'].values, train_predict, test_predict)
            
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 