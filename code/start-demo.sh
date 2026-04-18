#!/bin/bash
# 百度首页Demo启动脚本

echo "=================================================="
echo "       百度首页 Demo - 启动脚本"
echo "=================================================="
echo ""

# 检查Python版本
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "错误: 未找到Python，请先安装Python 3"
    exit 1
fi

# 检查文件是否存在
if [ ! -f "baidu-demo.html" ]; then
    echo "错误: 找不到 baidu-demo.html 文件"
    echo "请确保在正确的目录中运行此脚本"
    exit 1
fi

# 检查Python脚本是否存在
if [ ! -f "server.py" ]; then
    echo "错误: 找不到 server.py 文件"
    echo "请确保所有文件都在当前目录"
    exit 1
fi

echo "正在启动HTTP服务器..."
echo ""

# 启动服务器
$PYTHON_CMD server.py

echo ""
echo "=================================================="
echo "       百度首页 Demo - 已停止"
echo "=================================================="