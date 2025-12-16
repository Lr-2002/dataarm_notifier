#!/usr/bin/env python3
"""
USB报警灯控制器 - PyPI打包配置文件
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="dataarm-notifier",
    version="1.0.0",
    author="lr-2002",
    author_email="wang2629651228@gmail.com",
    description="USB报警灯控制器 - 支持控制红灯、绿灯、蓝灯以及颜色轮换",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YOUR_USERNAME/dataarm-notifier",
    project_urls={
        "Bug Tracker": "https://github.com/YOUR_USERNAME/dataarm-notifier/issues",
    },
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Hardware :: LEDs",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.6",
    packages=find_packages(),
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "usb-lamp=dataarm_notifier.usb_lamp_controller:main",
            "usb-lamp-server=dataarm_notifier.socket_server:main",
            "usb-lamp-client=dataarm_notifier.socket_client:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
