# 开发指南 - USB报警灯控制器

## 项目结构

```
usb-alarm-light/
├── usb_alarm_light/          # 主包目录
│   ├── __init__.py           # 包初始化文件
│   ├── usb_lamp_controller.py # 核心控制器
│   ├── socket_server.py      # Socket服务器
│   └── socket_client.py      # Socket客户端
├── tests/                    # 测试目录
│   ├── __init__.py
│   └── test_usb_lamp_controller.py
├── docs/                     # 文档目录（可选）
├── README.md                 # 项目说明
├── LICENSE                   # MIT许可证
├── requirements.txt          # 生产依赖
├── setup.py                  # 传统打包配置
├── pyproject.toml            # 现代打包配置
├── MANIFEST.in               # 包文件清单
├── .gitignore                # Git忽略文件
└── build_package.sh          # 打包脚本
```

## 开发环境设置

### 1. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows
```

### 2. 安装开发依赖

```bash
pip install -e ".[dev]"
```

这将安装：
- 生产依赖：pyserial
- 开发依赖：pytest, pytest-cov, black, flake8, build, twine

### 3. 运行测试

```bash
pytest tests/ -v
```

或运行覆盖率测试：

```bash
pytest tests/ --cov=usb_alarm_light --cov-report=html
```

### 4. 代码格式化

```bash
black usb_alarm_light/ tests/
```

### 5. 代码检查

```bash
flake8 usb_alarm_light/ tests/
```

## 打包到PyPI

### 1. 构建包

```bash
# 方法1: 使用脚本
./build_package.sh

# 方法2: 手动构建
python -m build
```

### 2. 检查包

```bash
twine check dist/*
```

### 3. 上传到Test PyPI（推荐先测试）

```bash
twine upload --repository testpypi dist/*
```

### 4. 上传到PyPI

```bash
twine upload dist/*
```

## PyPI账户设置

### 1. 注册PyPI账户

访问 https://pypi.org/account/register/ 注册账户

### 2. 创建API Token

1. 登录PyPI
2. 进入 Account Settings → API tokens
3. 创建新的API token
4. 将token保存到 `~/.pypirc` 文件：

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = <your-api-token>

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = <your-test-api-token>
```

## 版本管理

### 更新版本号

编辑以下文件中的版本号：

1. `pyproject.toml` - `version` 字段
2. `setup.py` - `version` 字段
3. `usb_alarm_light/__init__.py` - `__version__` 变量

### 版本号规则

使用语义化版本控制 (SemVer)：
- MAJOR.MINOR.PATCH
- MAJOR: 不兼容的API变更
- MINOR: 向后兼容的功能性变更
- PATCH: 向后兼容的问题修正

例如：1.0.0, 1.0.1, 1.1.0, 2.0.0

## 包的导入和使用

### 安装包

```bash
pip install usb-alarm-light
```

### 使用包

```python
from usb_alarm_light import USBLampController

controller = USBLampController(port='/dev/cu.usbserial-1330')
controller.set_red(on=True)
controller.start_color_cycle()
controller.stop_color_cycle()
controller.close()
```

### 命令行工具

安装包后会提供三个命令行工具：

```bash
# 直接运行控制器
usb-lamp

# 启动Socket服务器
usb-lamp-server

# 启动Socket客户端
usb-lamp-client
```

## 添加新功能

### 1. 修改代码

在 `usb_alarm_light/` 目录下修改相应文件

### 2. 添加测试

在 `tests/` 目录下添加或修改测试文件

### 3. 更新文档

更新 `README.md` 和相关文档

### 4. 测试

```bash
pytest tests/ -v
```

### 5. 构建和上传

```bash
./build_package.sh
twine upload dist/*
```

## 常见问题

### Q: 如何添加新的依赖？

A: 在 `pyproject.toml` 的 `dependencies` 列表中添加

### Q: 如何添加可选依赖？

A: 在 `pyproject.toml` 的 `project.optional-dependencies` 中添加

### Q: 如何添加命令行工具？

A: 在 `pyproject.toml` 的 `project.scripts` 中添加

### Q: 如何发布新版本？

A:
1. 更新版本号
2. 更新CHANGELOG
3. 创建Git tag
4. 构建包
5. 上传到PyPI

### Q: 如何处理不同操作系统的兼容性？

A:
- 在代码中使用 `os.path.join()` 构建路径
- 使用 `pathlib.Path` 处理路径
- 测试不同操作系统的串口设备路径

## 许可证

本项目使用MIT许可证，详见 `LICENSE` 文件。

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 联系方式

- 项目主页: https://github.com/yourusername/usb-alarm-light
- 问题跟踪: https://github.com/yourusername/usb-alarm-light/issues
- 邮箱: your.email@example.com
