"""Provides science mode mid level types"""

from typing import Sequence
from science_mode_4.protocol.channel_point import ChannelPoint
from science_mode_4.utils.byte_builder import ByteBuilder


class MidLevelChannelConfiguration():
    """Class for mid level channel configuration"""


    def __init__(self, is_active: bool = False, ramp: int = 0, period_in_ms: int = 0, points: Sequence[ChannelPoint] = None):
        self._is_active = is_active
        self._ramp = ramp
        self._period_in_ms = period_in_ms
        self._points: list[ChannelPoint] = [] if points is None else points


    def get_data(self) -> bytes:
        """Returns information as bytes"""
        if len(self._points) > 16:
            raise ValueError(f"Mid level update maximum of 16 points allowed {len(self.points)}")
        if (self._ramp < 0) or (self._ramp > 15):
            raise ValueError(f"Mid level update ramp must be between 0..15 {self.ramp}")
        if (self._period_in_ms < 0) or (self._period_in_ms > 32767 * 4):
            raise ValueError(f"Mid level update period must be between 0..131071 {self._period_in_ms}")

        period_factor = 2 if self._period_in_ms <= 32767 else 4
        bb = ByteBuilder()
        bb.set_bit_to_position(self._ramp, 0, 4)
        bb.set_bit_to_position(len(self._points) - 1, 4, 4)
        bb.set_bit_to_position(0 if period_factor == 2 else 1, 8, 1)
        bb.set_bit_to_position(self._period_in_ms * period_factor, 9, 15)
        bb.swap(1, 2)
        for x in self.points:
            bb.append_bytes(x.get_data())
        return bb.get_bytes()


    @property
    def is_active(self) -> bool:
        """Getter for is active"""
        return self._is_active


    @is_active.setter
    def is_active(self, is_active: bool):
        """Setter for is active"""
        self._is_active = is_active


    @property
    def ramp(self) -> int:
        """Getter for ramp"""
        return self._ramp


    @ramp.setter
    def ramp(self, ramp: int):
        """Setter for ramp"""
        self._ramp = ramp


    @property
    def period_in_ms(self) -> int:
        """Getter for period"""
        return self._period_in_ms


    @period_in_ms.setter
    def period_in_ms(self, period_in_ms: int):
        """Setter for period in ms"""
        self._period_in_ms = period_in_ms


    @property
    def points(self) -> list[ChannelPoint]:
        """Getter for points"""
        return self._points


    @points.setter
    def points(self, points: list[ChannelPoint]):
        """Setter for points"""
        self._points = points
