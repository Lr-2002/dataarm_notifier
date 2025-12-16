#!/usr/bin/env python3
"""
测试USB报警灯控制器
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataarm_notifier import USBLampController, LightColor


class TestUSBLampController(unittest.TestCase):
    """测试USBLampController类"""

    def setUp(self):
        """设置测试环境"""
        self.controller = USBLampController(port='/dev/ttyUSB0')

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.controller.port, '/dev/ttyUSB0')
        self.assertEqual(self.controller.baudrate, 4800)
        self.assertFalse(self.controller.red_on)
        self.assertFalse(self.controller.green_on)
        self.assertFalse(self.controller.blue_on)

    @patch('dataarm_notifier.usb_lamp_controller.USBLampController._send_command')
    @patch('dataarm_notifier.usb_lamp_controller.USBLampController.turn_off_all')
    @patch('dataarm_notifier.usb_lamp_controller.USBLampController.set_light_on')
    def test_set_red_on(self, mock_light_on, mock_turn_off, mock_send):
        """测试开启红灯"""
        mock_send.return_value = True
        self.controller.set_red(on=True)
        self.assertTrue(self.controller.red_on)
        mock_turn_off.assert_called_once()
        mock_light_on.assert_called_once_with(True)

    @patch('dataarm_notifier.usb_lamp_controller.USBLampController._send_command')
    def test_set_red_off(self, mock_send):
        """测试关闭红灯"""
        mock_send.return_value = True
        self.controller.set_red(on=False)
        self.assertFalse(self.controller.red_on)

    @patch('dataarm_notifier.usb_lamp_controller.USBLampController._send_command')
    @patch('dataarm_notifier.usb_lamp_controller.USBLampController.turn_off_all')
    @patch('dataarm_notifier.usb_lamp_controller.USBLampController.set_light_on')
    def test_set_green_on(self, mock_light_on, mock_turn_off, mock_send):
        """测试开启绿灯"""
        mock_send.return_value = True
        self.controller.set_green(on=True)
        self.assertTrue(self.controller.green_on)
        mock_turn_off.assert_called_once()
        mock_light_on.assert_called_once_with(True)

    @patch('dataarm_notifier.usb_lamp_controller.USBLampController._send_command')
    @patch('dataarm_notifier.usb_lamp_controller.USBLampController.turn_off_all')
    @patch('dataarm_notifier.usb_lamp_controller.USBLampController.set_light_on')
    def test_set_blue_on(self, mock_light_on, mock_turn_off, mock_send):
        """测试开启蓝灯"""
        mock_send.return_value = True
        self.controller.set_blue(on=True)
        self.assertTrue(self.controller.blue_on)
        mock_turn_off.assert_called_once()
        mock_light_on.assert_called_once_with(True)

    @patch('dataarm_notifier.usb_lamp_controller.USBLampController._send_command')
    def test_turn_off_all(self, mock_send):
        """测试关闭所有灯"""
        mock_send.return_value = True
        self.controller.set_red(on=True)
        self.controller.set_green(on=True)
        self.controller.set_blue(on=True)
        self.controller.turn_off_all()
        self.assertFalse(self.controller.red_on)
        self.assertFalse(self.controller.green_on)
        self.assertFalse(self.controller.blue_on)

    def test_get_status(self):
        """测试获取状态"""
        status = self.controller.get_status()
        self.assertIn('red', status)
        self.assertIn('green', status)
        self.assertIn('blue', status)
        self.assertIn('color_cycle', status)

    def test_crc16(self):
        """测试CRC16计算"""
        data = bytes([0x01, 0x06, 0x00, 0x08, 0x07, 0xCF])
        crc = self.controller._crc16(data)
        self.assertIsInstance(crc, bytes)
        self.assertEqual(len(crc), 2)

    def test_build_command(self):
        """测试构建命令"""
        cmd = self.controller._build_command(0x0008, 1999)
        self.assertIsInstance(cmd, bytes)
        self.assertEqual(len(cmd), 8)  # 地址+功能码+寄存器+数据+CRC = 8字节


if __name__ == '__main__':
    unittest.main()
