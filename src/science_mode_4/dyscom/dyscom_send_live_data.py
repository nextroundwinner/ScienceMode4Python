"""Provides packet classes for dyscom send live data"""

import struct
from science_mode_4.protocol.commands import Commands
from science_mode_4.protocol.packet import PacketAck
from .dyscom_types import DyscomElectrodeSample, DyscomSignalType, DyscomPowerLiveDataStatusFlag


class PacketDyscomSendLiveData(PacketAck):
    """Packet for dyscom send live data (this is technically not an acknowledge, but it is handled as such,
    because it is send automatically from device)"""


    def __init__(self, data: bytes):
        super().__init__(data)
        self._command = Commands.DL_SEND_LIVE_DATA
        self._number_of_channels = 0
        self._time_offset = 0
        self._samples: list[DyscomElectrodeSample] = []

        if not data is None:
            self._number_of_channels = data[0]
            self._time_offset = int.from_bytes(data[1:5], "big")

            for x in range(self._number_of_channels):
                start_index = 5 + x * 6

                sample = DyscomElectrodeSample()
                sample.value = struct.unpack_from(">f", data[start_index:start_index+4])[0]
                sample.signal_type = DyscomSignalType(data[start_index+4])
                status = data[start_index+5]
                for f in DyscomPowerLiveDataStatusFlag:
                    if status & f == f:
                        sample.status.add(f)

                self._samples.append(sample)


    @property
    def number_of_channels(self) -> int:
        """Getter for number of channels"""
        return self._number_of_channels


    @property
    def time_offset(self) -> int:
        """Getter for time offset"""
        return self._time_offset


    @property
    def samples(self) -> list[DyscomElectrodeSample]:
        """Getter for samples"""
        return self._samples


    @property
    def status_error(self) -> bool:
        """Returns true if in any sample a status flag is set, false otherwise"""
        for x in self._samples:
            if len(x.status) != 0:
                return True
        return False
