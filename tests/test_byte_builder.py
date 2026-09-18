"""Tests for ByteBuilder"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

from science_mode_4.utils.byte_builder import ByteBuilder


def test_default_init_is_empty():
    bb = ByteBuilder()
    assert len(bb) == 0
    assert bb.get_bytes() == b""


def test_init_with_value_and_byte_count():
    bb = ByteBuilder(0x1234, 2)
    # underlying BitVector stores bits LSB first -> little endian byte order
    assert bb.get_bytes() == (0x1234).to_bytes(2, "little")


def test_append_byte():
    bb = ByteBuilder()
    bb.append_byte(0x12)
    bb.append_byte(0xAB)
    assert bb.get_bytes() == bytes([0x12, 0xAB])


def test_append_bytes():
    bb = ByteBuilder()
    bb.append_bytes(bytes([0x01, 0x02, 0x03]))
    assert bb.get_bytes() == bytes([0x01, 0x02, 0x03])


def test_append_list():
    bb = ByteBuilder()
    bb.append_list([0x0A, 0x0B, 0x0C])
    assert bb.get_bytes() == bytes([0x0A, 0x0B, 0x0C])


def test_append_value_little_endian():
    bb = ByteBuilder()
    bb.append_value(0x1234, 2, do_swap=False)
    assert bb.get_bytes() == (0x1234).to_bytes(2, "little")


def test_append_value_big_endian():
    bb = ByteBuilder()
    bb.append_value(0x1234, 2, do_swap=True)
    assert bb.get_bytes() == (0x1234).to_bytes(2, "big")


def test_set_bit_to_position_extends_length():
    bb = ByteBuilder()
    bb.set_bit_to_position(1, 15, 1)
    # bit 15 is the last bit of the second byte
    assert len(bb) == 2
    assert bb.get_bytes() == bytes([0x00, 0x80])


def test_set_and_get_bit_from_position_round_trip():
    bb = ByteBuilder()
    value = 0b1101010110
    bb.set_bit_to_position(value, 10, 10)
    assert bb.get_bit_from_position(10, 10) == value
    # bits before the written range stay zero
    assert bb.get_bit_from_position(0, 10) == 0


def test_set_bytes_to_position():
    bb = ByteBuilder()
    bb.set_bytes_to_position(bytes([0xAA, 0xBB]), 1, 2)
    assert bb.get_bytes() == bytes([0x00, 0xAA, 0xBB])


def test_swap_reverses_byte_order():
    bb = ByteBuilder()
    bb.append_bytes(bytes([0x01, 0x02, 0x03, 0x04]))
    bb.swap(0, 4)
    assert bb.get_bytes() == bytes([0x04, 0x03, 0x02, 0x01])


def test_swap_only_affects_selected_range():
    bb = ByteBuilder()
    bb.append_bytes(bytes([0x01, 0x02, 0x03, 0x04]))
    bb.swap(1, 2)
    assert bb.get_bytes() == bytes([0x01, 0x03, 0x02, 0x04])


def test_extend_byte_builder_and_swap_matches_protocol_header_pattern():
    # mirrors the pattern used to build the command/packet-number prefix
    # in Protocol.packet_to_bytes: pack two 10/6 bit fields, then swap
    # the two resulting bytes into big endian order
    command = 0b0000010101  # 10 bits
    number = 0b000111        # 6 bits

    bb = ByteBuilder()
    bb.set_bit_to_position(command, 0, 10)
    bb.set_bit_to_position(number, 10, 6)
    bb.swap(0, 2)

    combined = command | (number << 10)
    assert bb.get_bytes() == combined.to_bytes(2, "little")[::-1]


def test_len_rounds_up_to_full_bytes():
    bb = ByteBuilder()
    bb.set_bit_to_position(1, 0, 1)
    assert len(bb) == 1

    bb.set_bit_to_position(1, 8, 1)
    assert len(bb) == 2


def test_clear_resets_builder():
    bb = ByteBuilder()
    bb.append_bytes(bytes([0x01, 0x02]))
    bb.clear()
    assert len(bb) == 0
    assert bb.get_bytes() == b""


def test_repr_and_str_contain_length_and_hex_bytes():
    bb = ByteBuilder()
    bb.append_bytes(bytes([0x01, 0x02]))
    assert "length: 2" in repr(bb)
    assert "01 02" in repr(bb)
    assert "length: 2" in str(bb)
    assert "01 02" in str(bb)
