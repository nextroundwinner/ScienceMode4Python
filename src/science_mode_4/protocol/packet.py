"""Provides base class for packets"""


from .commands import Commands


class Packet():
    """Base class for all packets"""


    def __init__(self):
        self._command = Commands.UNDEFINED
        self._kind = -1
        self._number = 0


    @property
    def command(self) -> Commands:
        """Getter for command"""
        return self._command


    @property
    def kind(self) -> int:
        """Getter for kind (to differentiate between multiple packages per command)"""
        return self._kind


    @property
    def number(self) -> int:
        """Getter for number"""
        return self._number


    @number.setter
    def number(self, value: int):
        """Setter for number"""
        self._number = value


    def get_data(self) -> bytes:
        """Return packet payload"""
        return bytes()


    def create_copy(self) -> "Packet":
        """Returns a copy"""
        return type(self)()


    def __repr__(self) -> str:
        return f"command: {self._command.name}, nr {self._number}"


    def __str__(self) -> str:
        return f"command: {self._command.name}, nr {self._number}"


class PacketAck(Packet):
    """Base class for all acknowledge packets"""


    def __init__(self, data: bytes):
        _ = data
        super().__init__()


    def get_kind(self, data: bytes) -> int:
        """Get kind from data, override in subclasses"""
        _ = data
        return -1


    def create_copy_with_data(self, data: bytes) -> "PacketAck":
        """Returns a copy with data"""
        return type(self)(data)
