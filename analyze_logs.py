def analyze_stock_logs(log_file_path):
    # 存储所有股票代码及其出现次数
    stock_counts = {}
    # 存储股票代码到股票名称的映射
    stock_names = {}
    
    current_strategy = ""
    
    with open(log_file_path, 'r', encoding='ansi') as file:
        for line in file:
            # 检测策略标记的开始
            if '**************"' in line:
                current_strategy = line.strip().replace('*', '').replace('"', '').strip()
                continue
                
            # 检测股票列表
            if line.startswith('[') and line.endswith(']\n'):
                # 解析股票代码和名称
                stocks = eval(line)  # 将字符串转换为列表
                for stock_tuple in stocks:
                    if len(stock_tuple) == 2:  # 确保是(代码,名称)的格式
                        code, name = stock_tuple
                        # 更新股票计数
                        stock_counts[code] = stock_counts.get(code, 0) + 1
                        # 保存股票名称
                        stock_names[code] = name

    # 筛选出现次数大于1的股票
    repeated_stocks = {code: count for code, count in stock_counts.items() if count > 1}
    
    # 按出现次数降序排序
    sorted_stocks = sorted(repeated_stocks.items(), key=lambda x: x[1], reverse=True)
    
    # 打印结果
    print("\n重复出现的股票：")
    print("股票代码  股票名称  出现次数")
    print("-" * 30)
    for code, count in sorted_stocks:
        print(f"{code}  {stock_names[code]}  {count}次")
    
    return sorted_stocks

# 使用示例
if __name__ == "__main__":
    log_file_path = "sequoia.log"  # 日志文件路径
    analyze_stock_logs(log_file_path) 