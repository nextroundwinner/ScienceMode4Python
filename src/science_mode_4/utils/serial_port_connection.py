"""Provides a class for a serial connection"""

import os
import time
import serial
import serial.tools.list_ports
import serial.tools.list_ports_common

from science_mode_4.utils.logger import logger
from .connection import Connection


class SerialPortConnection(Connection):
    """Serial connection class
    
    port: name of the device

    error_timeout: duration in seconds in case of an error between closing and opening connection
    """


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


    def __init__(self, port: str, read_timeout_ins_s: float = 0, write_timeout_ins_s: float = 1, error_timeout_in_s: float = 3):
        self._ser = serial.Serial(timeout = read_timeout_ins_s, write_timeout=write_timeout_ins_s)
        self._ser.port = port
        self._error_timeout_in_s = error_timeout_in_s

        self._last_written_data = bytes()


    @property
    def internal_serial(self) -> serial.Serial:
        """Getter for internal pySerial object"""
        return self._ser


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
        # store last written data, to be able to send it again
        self._last_written_data = data


    def clear_buffer(self):
        self._ser.reset_input_buffer()


    @property
    def ser(self) -> serial.Serial:
        """Getter for underlying serial object"""
        return self._ser


    def _read_intern(self) -> bytes:
        result = bytes()
        try:
            # may raise a ClearCommError / The device does not recognize the command.
            if self._ser.in_waiting > 0:
                result = self._ser.read_all()
        except serial.SerialException as e:
            logger().warning(e)

            logger().info("Close and open serial connection and write last written data again")
            # in case of a SerialException, close connection, open connection and
            # send last written data again
            try:
                self.close()
            except Exception: # pylint:disable=broad-exception-caught
                pass

            time.sleep(self._error_timeout_in_s)

            try:
                self.open()
            except Exception: # pylint:disable=broad-exception-caught
                pass

            # device did not recognize last written data, so send it again
            self.write(self._last_written_data)

        return result
