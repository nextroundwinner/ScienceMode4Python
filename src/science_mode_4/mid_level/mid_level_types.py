"""Provides science mode mid level types"""

from typing import Sequence
from science_mode_4.protocol.channel_point import ChannelPoint
from science_mode_4.utils.byte_builder import ByteBuilder


class MidLevelChannelConfiguration():
    """Class for mid level channel configuration"""


    def __init__(self, is_active: bool = False, ramp: int = 0, period_in_ms: float = 10.0, points: Sequence[ChannelPoint] = None):
        self._is_active = is_active
        self._ramp = ramp
        self._period_in_ms = period_in_ms
        self._points: list[ChannelPoint] = [] if points is None else points


    def get_data(self) -> bytes:
        """Returns information as bytes"""
        if len(self._points) == 0:
            raise ValueError(f"Mid level update at least one point required {len(self.points)}")
        if len(self._points) > 16:
            raise ValueError(f"Mid level update maximum of 16 points allowed {len(self.points)}")
        if (self._ramp < 0) or (self._ramp > 15):
            raise ValueError(f"Mid level update ramp must be between 0..15 {self.ramp}")
        # the 15 bit period field stores period_in_ms * period_factor, see the ScienceMode
        # protocol description of Ml_update ("Period in ms, value is calculated from transfer
        # function f(x) = 2x or f(x) = 4x, e.g. 1 ms -> 2"). Factor 4 gives finer 0.25ms
        # resolution, factor 2 gives coarser 0.5ms resolution, so factor 4 is used for the
        # smaller/more precise periods and factor 2 above that. The device datasheet documents
        # "Impulse repetition period: 0.5 - 16383 ms"; verified against a real P24 that this is
        # a hard limit enforced by the firmware (e.g. with factor 2, raw=32767 -> 16383.5ms is
        # rejected with a Parameter error, raw=32766 -> 16383ms is accepted), so 16383 is used
        # as the max regardless of factor rather than the theoretical 32767 / period_factor.
        period_factor = 4 if self._period_in_ms <= 8191 else 2
        max_period_in_ms = 16383
        # datasheet documents the minimum representable period as 0.5ms, not 0
        if (self._period_in_ms < 0.5) or (self._period_in_ms > max_period_in_ms):
            raise ValueError(f"Mid level update period must be between 0.5..{max_period_in_ms} {self._period_in_ms}")

        bb = ByteBuilder()
        bb.set_bit_to_position(self._ramp, 0, 4)
        bb.set_bit_to_position(len(self._points) - 1, 4, 4)
        bb.set_bit_to_position(0 if period_factor == 2 else 1, 8, 1)
        bb.set_bit_to_position(round(self._period_in_ms * period_factor), 9, 15)
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
    def period_in_ms(self) -> float:
        """Getter for period"""
        return self._period_in_ms


    @period_in_ms.setter
    def period_in_ms(self, period_in_ms: float):
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
