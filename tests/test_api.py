import pytest
import requests
import time
import random
from unittest.mock import patch

# API基础URL
API_BASE_URL = "http://localhost:8002"

# 模拟股票代码
TEST_STOCK_CODE = "000001"
TEST_STOCK_NAME = "平安银行"

# 跳过标记
skip_if_api_not_running = pytest.mark.skipif(
    True,  # 默认跳过，只有当API真正在运行时才会被设置为False
    reason="API服务器未运行"
)

@pytest.fixture(scope="session")
def check_api_running():
    """检查API服务器是否在运行"""
    try:
        response = requests.get(f"{API_BASE_URL}/system/health", timeout=2)
        if response.status_code == 200:
            # 如果API正在运行，则禁用跳过
            global skip_if_api_not_running
            skip_if_api_not_running = pytest.mark.skipif(False, reason="API服务器正在运行")
        return response.status_code == 200
    except requests.RequestException:
        return False

class TestStockAPI:
    """股票API测试"""
    
    @skip_if_api_not_running
    def test_search_stocks(self, check_api_running):
        """测试股票搜索API"""
        response = requests.get(f"{API_BASE_URL}/stocks/search?query={TEST_STOCK_NAME}")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        
        # 至少应当找到我们的测试股票
        matching_stocks = [stock for stock in data["data"] if stock["code"] == TEST_STOCK_CODE]
        assert len(matching_stocks) > 0
    
    @skip_if_api_not_running
    def test_get_stock_info(self, check_api_running):
        """测试获取股票信息API"""
        response = requests.get(f"{API_BASE_URL}/stocks/{TEST_STOCK_CODE}")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["code"] == TEST_STOCK_CODE
        
    @skip_if_api_not_running
    def test_get_stock_k_data(self, check_api_running):
        """测试获取股票K线数据API"""
        response = requests.get(f"{API_BASE_URL}/stocks/{TEST_STOCK_CODE}/kdata")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "kData" in data["data"]
        assert len(data["data"]["kData"]) > 0

class TestPredictionAPI:
    """预测API测试"""
    
    @skip_if_api_not_running
    def test_lstm_prediction(self, check_api_running):
        """测试LSTM预测API"""
        # 预测请求参数
        prediction_data = {
            "stockCode": TEST_STOCK_CODE,
            "stockName": TEST_STOCK_NAME,
            "predictionPeriod": 10,
            "modelConfig": "enhanced",
            "features": ["price", "volume", "technical"]
        }
        
        # 提交预测请求
        response = requests.post(f"{API_BASE_URL}/prediction/lstm", json=prediction_data)
        assert response.status_code == 200
        result = response.json()
        assert "data" in result
        assert "taskId" in result["data"]
        
        task_id = result["data"]["taskId"]
        
        # 检查任务状态
        max_attempts = 10
        for i in range(max_attempts):
            status_response = requests.get(f"{API_BASE_URL}/prediction/status/{task_id}")
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            # 如果任务完成或失败，停止等待
            if status_data["data"]["status"] in ["completed", "error"]:
                break
                
            # 等待一段时间后再次检查
            time.sleep(1)
            
        # 获取预测结果
        result_response = requests.get(f"{API_BASE_URL}/prediction/result/lstm/{task_id}")
        assert result_response.status_code == 200
        result_data = result_response.json()
        assert "data" in result_data
        
    @skip_if_api_not_running
    def test_get_prediction_history(self, check_api_running):
        """测试获取预测历史API"""
        response = requests.get(f"{API_BASE_URL}/prediction/history")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

class TestAnalysisAPI:
    """分析API测试"""
    
    @skip_if_api_not_running
    def test_get_available_strategies(self, check_api_running):
        """测试获取可用策略API"""
        response = requests.get(f"{API_BASE_URL}/analysis/strategies")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
    
    @skip_if_api_not_running
    def test_run_analysis(self, check_api_running):
        """测试运行分析API"""
        # 分析请求参数
        analysis_data = {
            "stocks": [{"code": TEST_STOCK_CODE, "name": TEST_STOCK_NAME}],
            "config": {
                "period": "daily",
                "dataLength": 120,
                "strategies": [
                    {"id": "rsrs", "params": {}}
                ]
            }
        }
        
        # 提交分析请求
        response = requests.post(f"{API_BASE_URL}/analysis/run", json=analysis_data)
        assert response.status_code == 200
        result = response.json()
        assert "data" in result
        assert "taskId" in result["data"]
        
        task_id = result["data"]["taskId"]
        
        # 检查任务状态
        max_attempts = 10
        for i in range(max_attempts):
            status_response = requests.get(f"{API_BASE_URL}/analysis/status/{task_id}")
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            # 如果任务完成或失败，停止等待
            if status_data["data"]["status"] in ["completed", "error"]:
                break
                
            # 等待一段时间后再次检查
            time.sleep(1)
        
        # 获取分析结果
        result_response = requests.get(f"{API_BASE_URL}/analysis/result/{TEST_STOCK_CODE}")
        assert result_response.status_code == 200
        result_data = result_response.json()
        assert "data" in result_data

    @skip_if_api_not_running
    def test_get_analysis_results(self, check_api_running):
        """测试获取分析结果API"""
        response = requests.get(f"{API_BASE_URL}/analysis")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

if __name__ == "__main__":
    # 检查API是否在运行
    import sys
    api_running = requests.get(f"{API_BASE_URL}/system/health", timeout=2).status_code == 200
    if not api_running:
        print("API服务器未运行，无法执行测试")
        sys.exit(1)
    
    # 运行单元测试
    pytest.main(["-xvs", __file__]) 