"""Provides packet classes for dyscom init"""

from typing import NamedTuple
from science_mode_4.dyscom.dyscom_helper import DyscomHelper
from science_mode_4.protocol.commands import Commands
from science_mode_4.protocol.types import ResultAndError
from science_mode_4.protocol.packet import Packet, PacketAck
from .dyscom_types import DyscomFrequencyOut, DyscomInitParams, DyscomInitState
from .ads129x.ads129x import Ads129x


class DyscomInitResult(NamedTuple):
    """Helper class for dyscom get with type file system status"""
    register_map_ads129x: Ads129x
    measurement_file_id: str
    init_state: DyscomInitState
    frequency_out: DyscomFrequencyOut


class PacketDyscomInit(Packet):
    """Packet for dyscom init"""


    def __init__(self, params: DyscomInitParams = DyscomInitParams()):
        super().__init__()
        self._command = Commands.DL_INIT
        self._params = params


    @property
    def params(self) -> DyscomInitParams:
        """Getter for params"""
        return self._params


    @params.setter
    def params(self, value: DyscomInitParams):
        """Setter for params"""
        self._params = value


    def get_data(self) -> bytes:
        return self._params.get_data()


class PacketDyscomInitAck(PacketAck):
    """Packet for dyscom init acknowledge"""


    def __init__(self, data: bytes):
        super().__init__(data)
        self._command = Commands.DL_INIT_ACK
        self._result_error = ResultAndError.NO_ERROR
        self._register_map_ads129x = Ads129x()
        self._measurement_file_id: str
        self._init_state = DyscomInitState.SUCCESS
        self._frequency_out = DyscomFrequencyOut.SAMPLES_PER_SECOND_4K

        if not data is None:
            self._result_error = ResultAndError(data[0])
            self._register_map_ads129x.set_data(data[1:27])
            self._measurement_file_id = DyscomHelper.bytes_to_str(data[27:87], 60)
            self._init_state = DyscomInitState(data[87])
            self._frequency_out = DyscomFrequencyOut(data[88])


    @property
    def result_error(self) -> ResultAndError:
        """Getter for ResultError"""
        return self._result_error


    @property
    def register_map_ads129x(self) -> Ads129x:
        """Getter for register map from ADS129x"""
        return self._register_map_ads129x


    @property
    def measurement_file_id(self) -> str:
        """Getter for measurement file id"""
        return self._measurement_file_id


    @property
    def init_state(self) -> DyscomInitState:
        """Getter for init state"""
        return self._init_state


    @property
    def frequency_out(self) -> DyscomFrequencyOut:
        """Getter for frequency out"""
        return self._frequency_out
