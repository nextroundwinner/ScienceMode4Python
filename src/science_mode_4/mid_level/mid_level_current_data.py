"""Provides packet classes for mid level GetCurrentData"""

from typing import NamedTuple

from science_mode_4.protocol.commands import Commands
from science_mode_4.protocol.packet import Packet, PacketAck
from science_mode_4.protocol.types import ResultAndError
from science_mode_4.utils.bit_vector import BitVector
from science_mode_4.utils.byte_builder import ByteBuilder


class MidLevelGetCurrentDataResult(NamedTuple):
    """Result for mid level get current data"""
    result_error: ResultAndError
    is_stimulation_active_per_channel: list[bool]
    channel_error: list[ResultAndError]


class PacketMidLevelGetCurrentData(Packet):
    """Packet for mid level GetCurrentData"""

    def __init__(self):
        super().__init__()
        self._command = Commands.MID_LEVEL_GET_CURRENT_DATA


    def get_data(self) -> bytes:
        bb = ByteBuilder()
        bb.append_byte(4)
        return bb.get_bytes()


class PacketMidLevelGetCurrentDataAck(PacketAck):
    """Packet for mid level GetCurrentData acknowledge"""


    def __init__(self, data: bytes):
        super().__init__(data)
        self._command = Commands.MID_LEVEL_GET_CURRENT_DATA_ACK
        self._result_error = ResultAndError.NO_ERROR
        self._data_selection = 0
        self._is_stimulation_active_per_channel = [False] * 8
        self._channel_error = [ResultAndError.NO_ERROR] * 8

        if not data is None:
            self._result_error = ResultAndError(data[0])
            # data selection should always be 4 (Returns all error from all channels)
            self._data_selection = data[1]
            self._is_stimulation_active_per_channel = [x != 0 for x in BitVector.init_from_int(data[2], 8)]
            bb = ByteBuilder()
            bb.append_bytes(data[3:7])
            for index, _ in enumerate(self._channel_error):
                tmp = bb.get_bit_from_position(index * 4, 4)
                if tmp == 0:
                    self._channel_error[index] = ResultAndError.NO_ERROR
                elif tmp == 1:
                    self._channel_error[index] = ResultAndError.ELECTRODE_ERROR
                elif tmp == 2:
                    self._channel_error[index] = ResultAndError.PULSE_TIMEOUT_ERROR
                elif tmp == 3:
                    self._channel_error[index] = ResultAndError.PULSE_LOW_CURRENT_ERROR


    @property
    def result_error(self) -> ResultAndError:
        """Getter for ResultError"""
        return self._result_error


    @property
    def is_stimulation_active_per_channel(self) -> list[bool]:
        """Getter for IsStimulationActive"""
        return self._is_stimulation_active_per_channel


    @property
    def channel_error(self) -> list[ResultAndError]:
        """Getter for ChannelError"""
        return self._channel_error
