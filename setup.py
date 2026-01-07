#!/usr/bin/env python3
"""
USB报警灯控制器 - PyPI打包配置文件
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    base_requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Telemetry module requirements
telemetry_requirements = [
    "rerun-sdk>=0.15.0",
    "opencv-python>=4.8.0",
    "pyyaml>=6.0",
    "numpy>=1.24.0",
]

all_requirements = base_requirements + telemetry_requirements

setup(
    name="dataarm-notifier",
    version="1.1.0",
    author="lr-2002",
    author_email="wang2629651228@gmail.com",
    description="USB报警灯控制器 + Robot Telemetry Visualization with Rerun SDK",
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
    install_requires=all_requirements,
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
            "telemetry=dataarm_notifier.cli.telemetry_cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
