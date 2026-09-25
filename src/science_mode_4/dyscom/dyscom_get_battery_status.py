"""Provides packet classes for dyscom get with type battery status"""

from typing import NamedTuple
import struct

from .dyscom_types import DyscomEnergyFlag, DyscomGetType
from .dyscom_get import PacketDyscomGet, PacketDyscomGetAck


class DyscomGetBatteryResult(NamedTuple):
    """Helper class for dyscom get with type file by name"""
    voltage: int
    current: int
    percentage: int
    temperature: int
    energy_state: set[DyscomEnergyFlag]


class PacketDyscomGetBatteryStatus(PacketDyscomGet):
    """Packet for dyscom get with type battery status"""


    def __init__(self):
        super().__init__()
        self._type = DyscomGetType.BATTERY
        self._kind = int(self._type)


class PacketDyscomGetAckBatteryStatus(PacketDyscomGetAck):
    """Packet for dyscom get for type battery status acknowledge"""


    def __init__(self, data: bytes):
        super().__init__(data)
        self._kind = int(DyscomGetType.BATTERY)
        self._voltage = 0
        self._current = 0
        self._percentage = 0
        self._temperature = 0
        self._energy_state: set[DyscomEnergyFlag] = set()

        if not data is None:
            energy_state, self._percentage, self._temperature, self._current, \
                self._voltage = struct.unpack("<BBbiI", data[2:13])

            for f in DyscomEnergyFlag:
                if f != DyscomEnergyFlag.UNDEFINED and energy_state & f == f:
                    self._energy_state.add(f)


    @property
    def voltage(self) -> int:
        """Getter for voltage, [0, 65535] in millivolt"""
        return self._voltage


    @property
    def current(self) -> int:
        """Getter for current, [-327675, 327675] in milliampere"""
        return self._current


    @property
    def percentage(self) -> int:
        """Getter for percentage, [0, 100] in percent"""
        return self._percentage


    @property
    def temperature(self) -> int:
        """Getter for temperature, [-128, 127] in degrees"""
        return self._temperature


    @property
    def energy_state(self) -> set[DyscomEnergyFlag]:
        """Getter for energy state"""
        return self._energy_state
