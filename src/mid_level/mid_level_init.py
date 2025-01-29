"""Provides classes for mid level Init"""

from src.protocol.commands import Commands, ResultAndError
from src.protocol.packet import Packet, PacketAck
from src.utils.byte_builder import ByteBuilder

class PacketMidLevelInit(Packet):
    """Packet for mid level Init"""


    def __init__(self):
        super().__init__()
        self._command = Commands.MidLevelInit
        self._do_stop_on_all_errors = False


    @property
    def do_stop_on_all_errors(self) -> bool:
        """Getter for do stop on all errors"""
        return self._do_stop_on_all_errors


    @do_stop_on_all_errors.setter
    def do_stop_on_all_errors(self, do_stop_on_all_errors: bool):
        """Setter for do stop on all errors"""
        self._do_stop_on_all_errors = do_stop_on_all_errors


    def get_data(self) -> bytes:
        bb = ByteBuilder()
        bb.append_byte(1 if self._do_stop_on_all_errors else 0)
        return bb.get_bytes()


class PacketMidLevelInitAck(PacketAck):
    """Packet for mid level Init acknowledge"""


    def __init__(self, data: bytes):
        super().__init__(data)
        self._command = Commands.MidLevelInitAck
        self._result_error = ResultAndError.NO_ERROR

        if data:
            self._result_error = ResultAndError(data[0])


    @property
    def result_error(self) -> ResultAndError:
        """Getter for ResultError"""
        return self._result_error
