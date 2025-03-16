"""Provides a ByteBuilder class for easier creation of a byte stream"""

from .bit_vector import BitVector


class ByteBuilder():
    """ByteBuilder class"""


    def __init__(self, data: int = 0, byte_count: int = 0):
        self.data = BitVector.init_from_int(data, byte_count * 8)


    def get_bit_from_position(self, bit_position: int, bit_count: int) -> int:
        """Returns bits starting with bit_position and a count of bit_count"""
        result = 0
        for x in range(bit_count):
            result |= (self.data[bit_position + x] << x)
        return result


    def append_byte(self, value: int):
        """Append a byte"""
        self._append_byte(value)


    def append_list(self, value: list[int]):
        """Extends current data with list of values (byte)"""
        for x in value:
            self._append_byte(x)


    def append_bytes(self, value: bytes):
        """Extends current data with value"""
        for x in value:
            self._append_byte(x)


    def extend_byte_builder(self, value: 'ByteBuilder'):
        """Extends current data with value"""
        self.data.extend(value.get_bytes())


    def set_bit_to_position(self, value: int, bit_position: int, bit_count: int):
        """
        Set bits starting with bit_position and a count of bit_count to value
        This method extends data to make room for value
        """
        new_length = max(len(self.data), bit_position + bit_count)
        self.data.set_length(new_length)
        for x in range(bit_count):
            self.data[bit_position + x] = (value >> x) & 0x1


    def set_bytes_to_position(self, value: bytes, byte_position: int, byte_count: int):
        """
        Set bytes starting with byte_position and a count of byte_count to value
        This method extends data to make room for value
        """
        for x in range(byte_count):
            self.set_bit_to_position(value[x], (byte_position + x) * 8, 8)


    def swap(self, start: int, count: int):
        """Swap bytes by reversion order from start to start + count"""
        tmp = self.get_bytes()
        for x in range(count):
            self.set_bit_to_position(tmp[start + x], (start + count - x - 1) * 8, 8)


    def get_bytes(self) -> bytes:
        """Returns data as bytes"""
        return self.data.get_bytes()


    def clear(self):
        """Resets data"""
        self.data = BitVector()


    def __repr__(self) -> str:
        b = self.get_bytes()
        return f"{len(b)} - {b.hex(' ').upper()}"


    def __str__(self) -> str:
        b = self.get_bytes()
        return f"{len(b)} - {b.hex(' ').upper()}"


    def _append_byte(self, value: int):
        """Append value at the end of data, value is treated as byte"""
        start = len(self.data)
        self.data.set_length(start + 8)
        for x in range(8):
            self.data[start + x] = (value >> x) & 0x1
