"""Tests for BitVector"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

import pytest

from science_mode_4.utils.bit_vector import BitVector


def test_default_init_is_empty():
    bv = BitVector()
    assert len(bv) == 0
    assert bv.get_bytes() == b""


def test_init_from_int_with_explicit_bit_length():
    # 0b1011 == 11, stored LSB first: bit0=1, bit1=1, bit2=0, bit3=1
    bv = BitVector.init_from_int(0b1011, 4)
    assert len(bv) == 4
    assert list(bv) == [1, 1, 0, 1]


def test_init_from_int_infers_bit_length_when_zero():
    # value.bit_length() for 0b1011 is 4
    bv = BitVector.init_from_int(0b1011, 0)
    assert len(bv) == 4


def test_getitem_returns_expected_bits():
    bv = BitVector.init_from_int(0b10, 2)
    assert bv[0] == 0
    assert bv[1] == 1


def test_getitem_out_of_bounds_raises():
    bv = BitVector.init_from_int(0, 4)
    with pytest.raises(ValueError):
        _ = bv[4]
    with pytest.raises(ValueError):
        _ = bv[-1]


def test_setitem_updates_bit():
    bv = BitVector.init_from_int(0, 4)
    bv[2] = 1
    assert list(bv) == [0, 0, 1, 0]


def test_setitem_out_of_bounds_raises():
    bv = BitVector.init_from_int(0, 4)
    with pytest.raises(ValueError):
        bv[4] = 1


def test_setitem_invalid_value_raises():
    bv = BitVector.init_from_int(0, 4)
    with pytest.raises(ValueError):
        bv[0] = 2


def test_set_length_grow_preserves_data_and_pads_with_zero():
    bv = BitVector.init_from_int(0b11, 2)
    bv.set_length(5)
    assert len(bv) == 5
    assert list(bv) == [1, 1, 0, 0, 0]


def test_set_length_shrink_truncates():
    bv = BitVector.init_from_int(0b1011, 4)
    bv.set_length(2)
    assert len(bv) == 2
    assert list(bv) == [1, 1]


def test_extend_appends_bits_from_other_bitvector():
    bv = BitVector.init_from_int(0b1, 1)
    bv.extend(BitVector.init_from_int(0b10, 2))
    assert list(bv) == [1, 0, 1]


def test_extend_ignores_non_bitvector_argument():
    # extend() silently does nothing if value is not a BitVector instance
    bv = BitVector.init_from_int(0b1, 1)
    bv.extend(b"\x01")
    assert list(bv) == [1]


def test_get_bytes_round_trips_full_bytes_little_endian():
    # bit_length is a multiple of 8, so get_bytes() matches int.to_bytes(..., "little")
    value = 0x1234
    bv = BitVector.init_from_int(value, 16)
    assert bv.get_bytes() == value.to_bytes(2, "little")


def test_get_bytes_pads_partial_last_byte():
    # 4 bits fit into a single byte, padded with zero in the high bits
    bv = BitVector.init_from_int(0b1011, 4)
    assert bv.get_bytes() == bytes([0b1011])


def test_iter_yields_all_bits_in_order():
    bv = BitVector.init_from_int(0b0110, 4)
    assert list(iter(bv)) == [0, 1, 1, 0]


def test_repr_shows_value_as_binary():
    bv = BitVector.init_from_int(0x1234, 16)
    assert repr(bv) == "BitVector(0b1_0010_0011_0100)"


def test_str_shows_value_as_binary():
    bv = BitVector.init_from_int(0b1011, 4)
    assert str(bv) == "0b1011"


def test_repr_and_str_of_empty_bitvector():
    bv = BitVector()
    assert repr(bv) == "BitVector(0b0)"
    assert str(bv) == "0b0"
