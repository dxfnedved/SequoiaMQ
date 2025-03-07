@echo off
echo 运行API测试...
python -m pytest tests/test_api.py -v

echo.
echo 运行策略测试...
python -m pytest tests/test_strategies.py -v

echo.
echo 测试完成! 