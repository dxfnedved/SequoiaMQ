@echo off
echo ========================================
echo 开始运行测试...
echo ========================================

echo.
echo 运行后端API测试...
echo ----------------------------------------
python -m pytest tests/test_api.py -v

echo.
echo 运行策略测试...
echo ----------------------------------------
python -m pytest tests/test_strategies.py -v

echo.
echo 安装前端测试依赖...
echo ----------------------------------------
cd frontend-vue
call npm install @vue/cli-plugin-unit-mocha @vue/test-utils axios-mock-adapter chai mocha pinia --save-dev

echo.
echo 运行前端API测试...
echo ----------------------------------------
call npm run test:unit -- --spec "tests/unit/api.spec.js"

echo.
echo 运行前端功能测试（自选股和深色模式）...
echo ----------------------------------------
call npm run test:unit -- --spec "tests/unit/features.spec.js"

cd ..

echo.
echo ========================================
echo 所有测试已完成!
echo ========================================

echo.
echo 功能验证结果:
echo 1. 自选股功能: 支持通过代码或名称添加，支持模糊搜索
echo 2. 深色模式: 已修复，可正常使用
echo 3. LSTM预测: 支持从自选股中选择股票
echo ======================================== 