"""Provides classes for mid level Update"""

from science_mode_4.protocol.commands import Commands
from science_mode_4.protocol.packet import Packet, PacketAck
from science_mode_4.protocol.types import ResultAndError
from science_mode_4.utils.byte_builder import ByteBuilder
from .mid_level_types import MidLevelChannelConfiguration


class PacketMidLevelUpdate(Packet):
    """Packet for mid level Update"""


    def __init__(self):
        super().__init__()
        self._command = Commands.MID_LEVEL_UPDATE
        self._channel_configuration: list[MidLevelChannelConfiguration] = [None] * 8


    @property
    def channel_configuration(self) -> list[MidLevelChannelConfiguration]:
        """Getter for channel configuration"""
        return self._channel_configuration


    @channel_configuration.setter
    def channel_configuration(self, channel_configuration: list[MidLevelChannelConfiguration]):
        """Setter for channel configuration"""
        if len(channel_configuration) > 8:
            raise ValueError(f"Mid level support 8 channels at max, given length {len(channel_configuration)}")
        self._channel_configuration = channel_configuration


    def get_data(self) -> bytes:
        bb = ByteBuilder()
        for x in range(8):
            c: MidLevelChannelConfiguration | None = self._channel_configuration[x] if x < len(self._channel_configuration) else None
            bb.set_bit_to_position(1 if c and c.is_active else 0, x, 1)

        for x in range(8):
            c: MidLevelChannelConfiguration | None = self._channel_configuration[x] if x < len(self._channel_configuration) else None
            if c is not None and c.is_active:
                bb.append_bytes(c.get_data())

        return bb.get_bytes()


class PacketMidLevelUpdateAck(PacketAck):
    """Packet for mid level Update acknowledge"""


    def __init__(self, data: bytes):
        super().__init__(data)
        self._command = Commands.MID_LEVEL_UPDATE_ACK
        self._result_error = ResultAndError.NO_ERROR

        if not data is None:
            self._result_error = ResultAndError(data[0])


    @property
    def result_error(self) -> ResultAndError:
        """Getter for ResultError"""
        return self._result_error
