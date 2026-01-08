"""Provides a class for a serial connection"""

import os
import serial
import serial.tools.list_ports
import serial.tools.list_ports_common

from science_mode_4.utils.logger import logger
from .connection import Connection


class SerialPortConnection(Connection):
    """Serial connection class"""


    @staticmethod
    def list_ports() -> list[serial.tools.list_ports_common.ListPortInfo]:
        """Returns a list of all serial ports"""
        return serial.tools.list_ports.comports()


    @staticmethod
    def list_science_mode_device_ports() -> list[serial.tools.list_ports_common.ListPortInfo]:
        """Returns a list of all serial ports with a science mode device"""
        ports = SerialPortConnection.list_ports()
        # science mode devices (P24/I24) have an STM32 mcu and these are
        # default values for USB CDC devices
        filtered_ports = list(filter(lambda x: x.vid == 0x0483 and x.pid == 0x5740, ports))
        return filtered_ports


    def __init__(self, port: str):
        self._ser = serial.Serial(timeout = 0)
        self._ser.port = port


    def open(self):
        self._ser.open()

        if os.name == "nt":
            self._ser.set_buffer_size(4096*128)


    def close(self):
        self._ser.close()


    def is_open(self) -> bool:
        return self._ser.is_open


    def write(self, data: bytes):
        super().write(data)
        self._ser.write(data)


    def clear_buffer(self):
        self._ser.reset_input_buffer()


    def _read_intern(self) -> bytes:
        result = bytes()
        try:
            # may raise a ClearCommError / The device does not recognize the command.
            if self._ser.in_waiting > 0:
                result = self._ser.read_all()
        except serial.SerialException as e:
            logger().warning(e)

        return result
