"""Provides a simple BitVector class"""


class BitVector():
    """Simple bitvector class"""


    @staticmethod
    def init_from_int(value: int = 0, bit_length: int = 0) -> "BitVector":
        """Creates new BitVector instance from an integer value with bit_length"""
        result = BitVector()
        result.set_from_int(value, bit_length)
        return result


    def __init__(self):
        self._data: list[int] = []
        self._current = 0

        self.set_from_int(0, 0)


    def set_from_int(self, value: int = 0, bit_length: int = 0):
        """Set to an integer value with bit_length"""
        bl = bit_length
        if bl == 0:
            bl = value.bit_length()
        self._data = [0] * bl

        for x in range(bl):
            self._data[x] = (value >> x) & 0x1


    def __getitem__(self, index: int) -> int:
        if (index < 0) or (index >= len(self._data)):
            raise ValueError(f"Bit vector index out of bounds {index} [0 - {len(self._data)}]")

        return self._data[index]


    def __setitem__(self, index: int, value: int):
        if not value in {0, 1}:
            raise ValueError(f"Bit vector wrong value {value}")
        if (index < 0) or (index >= len(self._data)):
            raise ValueError(f"Bit vector index out of bounds {index} [0 - {len(self._data)}]")

        self._data[index] = value


    def __len__(self) -> int:
        return len(self._data)


    def __iter__(self):
        yield from self._data


    def set_length(self, new_length: int):
        """Set length to new_length, does preserve current data"""
        length_difference = new_length - len(self._data)
        if length_difference > 0:
            self.extend(BitVector.init_from_int(0, length_difference))
        elif length_difference < 0:
            self._data = self._data[0:new_length]


    def extend(self, value: "BitVector"):
        """Extends current data with value"""
        if isinstance(value, BitVector):
            self._data += value._data # pylint: disable=protected-access


    def get_bytes(self) -> bytes:
        """Convert to bytes"""
        result = bytearray()
        position = 0

        value = 0
        bit_counter = 0
        bl = len(self._data)
        while position < bl:
            if bit_counter == 8:
                result.append(value)
                value = 0
                bit_counter = 0

            value |= self[position] << bit_counter
            position += 1
            bit_counter += 1

        if bit_counter > 0:
            result.append(value)

        return bytes(result)


    def __repr__(self) -> str:
        value = int.from_bytes(self.get_bytes(), "little")
        return f"{type(self).__name__}(0b{value:_b})"


    def __str__(self) -> str:
        value = int.from_bytes(self.get_bytes(), "little")
        return "0b" + format(value, "_b")
