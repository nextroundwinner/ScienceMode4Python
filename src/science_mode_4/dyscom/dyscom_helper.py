"""Helper class for dyscom"""

import struct
import datetime
from science_mode_4.utils.byte_builder import ByteBuilder


class DyscomHelper:
    """Provides some helper functions"""

    _unpack_func = struct.Struct("<BBBBBBBHh").unpack

    @staticmethod
    def datetime_to_bytes(dt: datetime.datetime) -> bytes:
        """Converts a datetime into dyscom compatible bytes"""
        bb = ByteBuilder()
        bb.append_byte(dt.hour)
        dst = dt.dst()
        bb.append_byte(0 if dst is None or dst == 0 else 1)
        bb.append_byte(dt.day)
        bb.append_byte(dt.minute)
        bb.append_byte(dt.month)
        bb.append_byte(dt.second)
        bb.append_byte((dt.weekday() + 1) % 7)
        bb.append_value(dt.timetuple().tm_yday - 1, 2, True)
        bb.append_value(dt.year - 1900, 2, True)

        return bb.get_bytes()


    @staticmethod
    def bytes_to_datetime(data: bytes) -> datetime.datetime:
        """Converts dyscom datetime bytes to a datetime"""
        # pylint:disable=unused-variable
        hour, dst, day, minute, month, second, _, _, year_since_1900 = \
            DyscomHelper._unpack_func(data)

        # do we need to consider dst?
        result = datetime.datetime(1900 + year_since_1900, month, day, hour, minute, second)
        return result


    @staticmethod
    def str_to_bytes(value: str, byte_count: int) -> bytes:
        """Converts value to bytes with byte_count bytes, last byte will always be 0"""
        if len(value) > byte_count - 1:
            raise ValueError(f"Value '{value}' is too long, maximum length is {byte_count - 1} characters")

        temp = bytearray(byte_count)
        for x in range(byte_count):
            if x < len(value):
                temp[x] = ord(value[x])
            else:
                temp[x] = 0
        temp[byte_count-1] = 0
        return bytes(temp)


    @staticmethod
    def bytes_to_str(value: bytes, byte_count: int) -> str:
        """Converts bytes to str with byte_count bytes"""
        end = value.find(bytes([0]))
        if end == -1:
            end = byte_count
        return value[0:end].decode()
