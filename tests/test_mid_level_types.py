"""Tests for MidLevelChannelConfiguration"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

import pytest

from science_mode_4.mid_level.mid_level_types import MidLevelChannelConfiguration
from science_mode_4.protocol.channel_point import ChannelPoint
from science_mode_4.utils.byte_builder import ByteBuilder

_SOME_POINT = ChannelPoint(100, 10.0)


def _decode_period(data: bytes) -> tuple[int, int]:
    """Returns (encoded_period_ms, period_factor) from encoded channel configuration bytes"""
    bb = ByteBuilder()
    bb.append_bytes(data)
    bb.swap(1, 2)
    factor = 4 if bb.get_bit_from_position(8, 1) == 1 else 2
    raw = bb.get_bit_from_position(9, 15)
    return raw * factor, factor


def test_period_in_ms_does_not_overflow_for_max_documented_value():
    # regression test: the period field used to be encoded as
    # "period_in_ms * period_factor" instead of "period_in_ms / period_factor",
    # so it silently overflowed the 15 bit field (BitVector truncates without
    # raising) for almost the whole documented 0..131068 range
    config = MidLevelChannelConfiguration(period_in_ms=32767 * 4, points=[_SOME_POINT])
    data = config.get_data()

    decoded, factor = _decode_period(data)
    assert factor == 4
    assert decoded == 32767 * 4


@pytest.mark.parametrize("period_in_ms", [0, 1, 100, 20000, 32767, 40000, 65534, 100000, 131068])
def test_period_in_ms_encodes_without_overflow(period_in_ms):
    config = MidLevelChannelConfiguration(period_in_ms=period_in_ms, points=[_SOME_POINT])
    data = config.get_data()

    decoded, _ = _decode_period(data)
    # allowed to round to the nearest representable step of period_factor (2 or 4 ms),
    # but must never wrap around due to a 15 bit overflow
    assert abs(decoded - period_in_ms) < 4


def test_period_in_ms_uses_factor_2_at_and_below_threshold():
    config = MidLevelChannelConfiguration(period_in_ms=32767, points=[_SOME_POINT])
    _, factor = _decode_period(config.get_data())
    assert factor == 2


def test_period_in_ms_uses_factor_4_above_threshold():
    config = MidLevelChannelConfiguration(period_in_ms=32768, points=[_SOME_POINT])
    _, factor = _decode_period(config.get_data())
    assert factor == 4


def test_get_data_raises_for_period_above_max():
    config = MidLevelChannelConfiguration(period_in_ms=32767 * 4 + 1, points=[_SOME_POINT])
    with pytest.raises(ValueError):
        config.get_data()


def test_get_data_raises_for_negative_period():
    config = MidLevelChannelConfiguration(period_in_ms=-1, points=[_SOME_POINT])
    with pytest.raises(ValueError):
        config.get_data()
