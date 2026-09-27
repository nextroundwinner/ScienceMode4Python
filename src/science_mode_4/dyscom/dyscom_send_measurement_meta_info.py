"""Provides packet classes for dyscom send measurement meta info"""

import datetime
from science_mode_4.protocol.commands import Commands
from science_mode_4.protocol.packet import PacketAck
from .dyscom_helper import DyscomHelper
from .dyscom_types import DyscomInitParams


class PacketDyscomSendMeasurementMetaInfo(PacketAck):
    """Packet for dyscom send measurement meta info (this is technically not an acknowledge, but it is handled as such,
    because it is send automatically from device).
    Note: I24 firmware never sends this packet"""


    def __init__(self, data: bytes):
        super().__init__(data)
        self._command = Commands.DL_MMI
        self._init_params: DyscomInitParams = DyscomInitParams()
        self._file_name = ""
        self._file_size = 0
        self._file_number = 0
        self._proband_name = ""
        self._start_time = datetime.datetime.now()
        self._duration = datetime.timedelta()

        if not data is None:
            self._init_params.set_data(data[0:361])
            self._file_name = DyscomHelper.bytes_to_str(data[361:421], 60)
            self._file_size = int.from_bytes(data[421:429], "big")
            self._file_number = int.from_bytes(data[429:431], "big")
            self._proband_name = DyscomHelper.bytes_to_str(data[431:468], 37)
            self._start_time = DyscomHelper.bytes_to_datetime(data[468:479])
            self._duration = datetime.timedelta(seconds=int.from_bytes(data[479:483]))


    @property
    def init_params(self) -> DyscomInitParams:
        """Getter for init params"""
        return self._init_params


    @property
    def file_name(self) -> str:
        """Getter for file id"""
        return self._file_name


    @property
    def file_size(self) -> int:
        """Getter for file size"""
        return self._file_size


    @property
    def file_number(self) -> int:
        """Getter for file number"""
        return self._file_number


    @property
    def proband_name(self) -> str:
        """Getter for proband name"""
        return self._proband_name


    @property
    def start_time(self) -> datetime.datetime:
        """Getter for start time"""
        return self._start_time


    @property
    def duration(self) -> datetime.timedelta:
        """Getter for duration"""
        return self._duration
