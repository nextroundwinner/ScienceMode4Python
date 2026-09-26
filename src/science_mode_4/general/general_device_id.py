"""Provides classes for general GetDeviceId"""

from science_mode_4.protocol.types import ResultAndError
from science_mode_4.protocol.commands import Commands
from science_mode_4.protocol.packet import Packet, PacketAck

class PacketGeneralGetDeviceId(Packet):
    """Packet for general GetDeviceId"""


    def __init__(self):
        super().__init__()
        self._command = Commands.GET_DEVICE_ID


class PacketGeneralGetDeviceIdAck(PacketAck):
    """Packet for general GetDeviceId acknowledge"""


    def __init__(self, data: bytes):
        super().__init__(data)
        self._command = Commands.GET_DEVICE_ID_ACK
        self._result_error = ResultAndError.NO_ERROR
        self._device_id = ""

        if not data is None:
            self._result_error = ResultAndError(data[0])
            # device id is a fixed 10 byte char array, null padded/terminated -> strip
            # the padding so callers don't get a trailing "\x00" in the string
            raw_device_id = data[1:11]
            end = raw_device_id.find(b"\x00")
            self._device_id = raw_device_id[:end if end != -1 else len(raw_device_id)].decode()


    @property
    def result_error(self) -> ResultAndError:
        """Getter for ResultError"""
        return self._result_error


    @property
    def device_id(self) -> str:
        """Getter for DeviceId"""
        return self._device_id
