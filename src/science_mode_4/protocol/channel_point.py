"""Provides science mode type channel point"""

from science_mode_4.utils.byte_builder import ByteBuilder


class ChannelPoint():
    """Class for channel point"""


    def __init__(self, duration_micro_seconds: int, current_milli_ampere: float):
        self._duration_in_micro_seconds = duration_micro_seconds
        self._current_in_milli_ampere = current_milli_ampere


    @property
    def current_in_milli_ampere(self) -> float:
        """Getter for current"""
        return self._current_in_milli_ampere


    @current_in_milli_ampere.setter
    def current_in_milli_ampere(self, value: float):
        """Setter for current"""
        self._current_in_milli_ampere = value


    @property
    def duration_in_micro_seconds(self) -> int:
        """Getter for duration"""
        return self._duration_in_micro_seconds


    @duration_in_micro_seconds.setter
    def duration_in_micro_seconds(self, value: int):
        """Setter for duration"""
        self._duration_in_micro_seconds = value


    def get_data(self) -> bytes:
        """Convert information to bytes"""
        if (self._current_in_milli_ampere < -150.0) or (self._current_in_milli_ampere > 150.0):
            raise ValueError(f"Channel point current must be between -150..150 {self._current_in_milli_ampere}")
        if (self._duration_in_micro_seconds < 0) or (self._duration_in_micro_seconds > 4095):
            raise ValueError(f"Channel point duration must be between 0..4095 {self._duration_in_micro_seconds}")

        c = round(2.0 * self._current_in_milli_ampere + 300.0)

        bb = ByteBuilder()
        bb.set_bit_to_position(0, 0, 10)
        bb.set_bit_to_position(c, 10, 10)
        bb.set_bit_to_position(self._duration_in_micro_seconds, 20, 12)
        bb.swap(0, 4)
        return bb.get_bytes()
