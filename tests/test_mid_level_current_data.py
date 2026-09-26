"""Tests for PacketMidLevelGetCurrentDataAck"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

import pytest

from science_mode_4.mid_level.mid_level_current_data import PacketMidLevelGetCurrentDataAck
from science_mode_4.protocol.exceptions import ProtocolError
from science_mode_4.protocol.types import ResultAndError
from science_mode_4.utils.byte_builder import ByteBuilder


def _build_data(result_error: int, active_mask: int, channel_error_nibbles: list[int]) -> bytes:
    assert len(channel_error_nibbles) == 8
    bb = ByteBuilder()
    for index, nibble in enumerate(channel_error_nibbles):
        bb.set_bit_to_position(nibble, index * 4, 4)
    channel_error_bytes = bb.get_bytes().ljust(4, b"\x00")
    return bytes([result_error, 4, active_mask]) + channel_error_bytes


def test_channel_error_decodes_defined_codes():
    data = _build_data(0, 0, [0, 1, 2, 3, 0, 0, 0, 0])
    ack = PacketMidLevelGetCurrentDataAck(data)

    assert ack.channel_error[0] == ResultAndError.NO_ERROR
    assert ack.channel_error[1] == ResultAndError.ELECTRODE_ERROR
    assert ack.channel_error[2] == ResultAndError.PULSE_TIMEOUT_ERROR
    assert ack.channel_error[3] == ResultAndError.PULSE_LOW_CURRENT_ERROR


@pytest.mark.parametrize("unknown_code", [4, 5, 10, 15])
def test_channel_error_raises_for_undefined_codes_instead_of_silently_reporting_no_error(unknown_code):
    # regression test: codes 4-15 used to fall through the if/elif chain and leave
    # channel_error at its pre-initialized NO_ERROR default, silently masking a
    # channel error the device actually reported
    nibbles = [0] * 8
    nibbles[5] = unknown_code
    data = _build_data(0, 0, nibbles)

    with pytest.raises(ProtocolError):
        PacketMidLevelGetCurrentDataAck(data)


def test_channel_error_defaults_to_no_error_without_data():
    ack = PacketMidLevelGetCurrentDataAck(None)
    assert ack.channel_error == [ResultAndError.NO_ERROR] * 8
