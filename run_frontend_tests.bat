@echo off
echo 运行前端测试...
cd frontend-vue

echo 安装依赖...
call npm install

echo 运行单元测试...
call npm run test:unit

echo.
echo 测试完成!
echo 如果测试通过，说明自选股功能和深色模式功能已正常实现。 