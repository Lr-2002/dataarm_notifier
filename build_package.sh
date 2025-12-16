#!/bin/bash
# USB报警灯控制器 - PyPI打包脚本

echo "=========================================="
echo "USB报警灯控制器 - PyPI打包脚本"
echo "=========================================="

# 检查Python版本
echo "\n1. 检查Python版本..."
python3 --version

# 安装打包工具
echo "\n2. 安装打包工具..."
pip install build twine

# 运行测试
echo "\n3. 运行测试..."
python -m pytest tests/ -v

# 构建包
echo "\n4. 构建包..."
python -m build

# 检查包
echo "\n5. 检查包..."
twine check dist/*

echo "\n=========================================="
echo "打包完成！"
echo "=========================================="
echo "\n要上传到PyPI，请运行:"
echo "  twine upload dist/*"
echo "\n或者先测试上传到Test PyPI:"
echo "  twine upload --repository testpypi dist/*"
echo "\n=========================================="
