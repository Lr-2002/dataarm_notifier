# PyPI打包指南 - USB报警灯控制器

## 项目已完成PyPI打包准备！

本指南将带你完成将USB报警灯控制器打包并发布到PyPI的全过程。

## 📁 项目结构

```
usb-alarm-light/
├── usb_alarm_light/          # 主包
│   ├── __init__.py           # 包初始化，导出USBLampController
│   ├── usb_lamp_controller.py # 核心控制器
│   ├── socket_server.py      # Socket服务器
│   └── socket_client.py      # Socket客户端
├── tests/                    # 测试
│   ├── __init__.py
│   └── test_usb_lamp_controller.py
├── docs/                     # 文档（可选）
├── README.md                 # 完整文档
├── LICENSE                   # MIT许可证
├── CHANGELOG.md              # 更新日志
├── requirements.txt          # 依赖
├── setup.py                  # 传统打包配置
├── pyproject.toml            # 现代打包配置
├── MANIFEST.in               # 包文件清单
├── .gitignore                # Git忽略文件
├── build_package.sh          # 打包脚本
├── DEVELOPMENT.md            # 开发指南
├── example.py                # 使用示例
└── PYPI_README.md            # PyPI专用README
```

## 🚀 打包步骤

### 1. 安装打包工具

```bash
pip install build twine
```

### 2. 准备PyPI账户

#### 注册PyPI账户
访问 https://pypi.org/account/register/ 注册账户

#### 创建API Token
1. 登录PyPI (https://pypi.org)
2. 进入 Account Settings → API tokens
3. 创建新的API token（Scope: Entire account）
4. 保存token（格式：pypi-xxxxx）

#### 配置认证
创建 `~/.pypirc` 文件：

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-api-token-here
```

### 3. 准备发布

#### 更新版本号
编辑以下文件中的版本号（保持一致）：
- `pyproject.toml` - `version`
- `setup.py` - `version`
- `usb_alarm_light/__init__.py` - `__version__`

#### 更新作者信息
在以下文件中更新作者信息：
- `pyproject.toml` - `authors`, `maintainers`
- `setup.py` - `author`, `author_email`
- `usb_alarm_light/__init__.py` - `__author__`, `__email__`

#### 更新GitHub链接
在以下文件中更新GitHub链接：
- `pyproject.toml` - `url`, `project_urls`
- `README.md` - 文档链接
- `PYPI_README.md` - GitHub链接

### 4. 构建包

```bash
# 方法1: 使用脚本（推荐）
./build_package.sh

# 方法2: 手动构建
python -m build

# 方法3: 仅构建源码包
python setup.py sdist bdist_wheel
```

### 5. 检查包

```bash
twine check dist/*
```

### 6. 测试上传（推荐）

先上传到Test PyPI测试：

```bash
twine upload --repository testpypi dist/*
```

然后安装测试：

```bash
pip install --index-url https://test.pypi.org/simple/ usb-alarm-light
```

### 7. 上传到PyPI

```bash
twine upload dist/*
```

## 📦 包信息

### 包名
- **PyPI包名**: `usb-alarm-light`
- **导入名**: `from usb_alarm_light import USBLampController`

### 版本
- **当前版本**: 1.0.0
- **版本规则**: 语义化版本控制 (MAJOR.MINOR.PATCH)

### 依赖
- **Python版本**: >=3.6
- **主要依赖**: pyserial >= 3.5

### 分类
- Development Status :: 4 - Beta
- Intended Audience :: Developers
- License :: OSI Approved :: MIT License
- Operating System :: OS Independent
- Programming Language :: Python :: 3.6+
- Topic :: Hardware :: LEDs
- Topic :: Software Development :: Libraries :: Python Modules

## 🛠️ 安装后使用

### 方式1: Python代码

```python
from usb_alarm_light import USBLampController

controller = USBLampController(port='/dev/cu.usbserial-1330')
controller.set_red(on=True)
controller.start_color_cycle()
controller.stop_color_cycle()
controller.close()
```

### 方式2: 命令行工具

```bash
# 直接运行控制器
usb-lamp

# 启动Socket服务器
usb-lamp-server

# 启动Socket客户端
usb-lamp-client
```

## 🔄 版本更新流程

1. **修改代码**
2. **更新版本号**（所有文件）
3. **更新CHANGELOG.md**
4. **提交Git变更**
5. **创建Git tag**: `git tag v1.0.0`
6. **推送tag**: `git push origin v1.0.0`
7. **构建包**: `./build_package.sh`
8. **上传到PyPI**: `twine upload dist/*`

## 📊 包大小

构建后的包大约：
- 源码包 (`.tar.gz`): ~20 KB
- wheel包 (`.whl`): ~15 KB

## 🧪 测试

### 运行测试套件

```bash
pytest tests/ -v
```

### 测试覆盖率

```bash
pytest tests/ --cov=usb_alarm_light --cov-report=html
```

## 📝 注意事项

### 包名检查
在发布前确认包名可用：
- 检查 https://pypi.org/project/usb-alarm-light
- 确认没有重名包

### 版本号规则
- 1.0.0 - 首次发布
- 1.0.1 - Bug修复
- 1.1.0 - 新功能（向后兼容）
- 2.0.0 - 破坏性变更

### 依赖管理
- 只包含必要的运行时依赖
- 开发依赖使用 `extras_require`

### 文档
- README是PyPI的展示页面
- 包含徽章和示例
- 清晰的使用说明

## 🎯 快速参考

### 常用命令

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 格式化代码
black usb_alarm_light/ tests/

# 检查代码
flake8 usb_alarm_light/ tests/

# 构建包
python -m build

# 检查包
twine check dist/*

# 上传到Test PyPI
twine upload --repository testpypi dist/*

# 上传到PyPI
twine upload dist/*
```

### 文件清单

- ✅ setup.py - 传统打包配置
- ✅ pyproject.toml - 现代打包配置
- ✅ MANIFEST.in - 包含文件清单
- ✅ README.md - 项目文档
- ✅ LICENSE - MIT许可证
- ✅ CHANGELOG.md - 版本更新记录
- ✅ .gitignore - Git忽略文件
- ✅ tests/ - 测试套件
- ✅ example.py - 使用示例
- ✅ build_package.sh - 打包脚本

## 🎉 发布完成

包发布后，用户可以：

```bash
# 安装
pip install usb-alarm-light

# 使用
from usb_alarm_light import USBLampController
```

## 📞 支持

- **文档**: https://github.com/yourusername/usb-alarm-light
- **问题**: https://github.com/yourusername/usb-alarm-light/issues
- **邮箱**: your.email@example.com

---

**祝打包成功！** 🚀
