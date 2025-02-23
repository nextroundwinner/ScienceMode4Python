"""Provides classes for general UnkownCommand"""

from ..protocol.commands import Commands
from ..protocol.packet import PacketAck
from ..types.result_and_error import ResultAndError


class PacketGeneralUnknownCommand(PacketAck):
    """Packet for general UnknownCommand"""


    def __init__(self, data: bytes):
        super().__init__(data)
        self._command = Commands.UnkownCommand
        self._result_error = ResultAndError.NO_ERROR

        if not data is None:
            self._result_error = ResultAndError(data[0])


    @property
    def result_error(self) -> ResultAndError:
        """Getter for ResultError"""
        return self._result_error
