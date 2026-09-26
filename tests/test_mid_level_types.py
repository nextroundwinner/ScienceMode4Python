"""Tests for MidLevelChannelConfiguration"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

import pytest

from science_mode_4.mid_level.mid_level_types import MidLevelChannelConfiguration
from science_mode_4.protocol.channel_point import ChannelPoint
from science_mode_4.utils.byte_builder import ByteBuilder

_SOME_POINT = ChannelPoint(100, 10.0)

# threshold below/at which factor 4 (0.25ms resolution) is used, above which factor 2
# (0.5ms resolution, larger range) is used
_FACTOR_4_THRESHOLD_IN_MS = 8191
# matches the P24 datasheet: "Impulse repetition period: 0.5 - 16383 ms". Verified against
# a real P24: this is a hard 16383ms limit, not 32767 / 2 (16383.5) as the raw 15 bit field
# would theoretically allow - the device rejects raw=32767 (16383.5ms) with a Parameter error
_MAX_PERIOD_IN_MS = 16383


def _decode_period(data: bytes) -> tuple[float, int]:
    """Returns (decoded_period_ms, period_factor) from encoded channel configuration bytes.
    Per the ScienceMode protocol description (Ml_update): the 15 bit raw field stores
    period_in_ms * period_factor ("value is calculated from transfer function f(x) = 2x or
    f(x) = 4x, e.g. 1 ms -> 2"), so decoding divides the raw value by the factor again."""
    bb = ByteBuilder()
    bb.append_bytes(data)
    bb.swap(1, 2)
    factor = 4 if bb.get_bit_from_position(8, 1) == 1 else 2
    raw = bb.get_bit_from_position(9, 15)
    return raw / factor, factor


def test_period_in_ms_uses_factor_4_at_and_below_threshold():
    config = MidLevelChannelConfiguration(period_in_ms=_FACTOR_4_THRESHOLD_IN_MS, points=[_SOME_POINT])
    decoded, factor = _decode_period(config.get_data())
    assert factor == 4
    assert decoded == _FACTOR_4_THRESHOLD_IN_MS


def test_period_in_ms_uses_factor_2_above_threshold():
    config = MidLevelChannelConfiguration(period_in_ms=_FACTOR_4_THRESHOLD_IN_MS + 1, points=[_SOME_POINT])
    decoded, factor = _decode_period(config.get_data())
    assert factor == 2
    assert decoded == _FACTOR_4_THRESHOLD_IN_MS + 1


def test_period_in_ms_supports_quarter_millisecond_resolution_with_factor_4():
    config = MidLevelChannelConfiguration(period_in_ms=1.25, points=[_SOME_POINT])
    decoded, factor = _decode_period(config.get_data())
    assert factor == 4
    assert decoded == 1.25


def test_period_in_ms_supports_half_millisecond_resolution_with_factor_2():
    config = MidLevelChannelConfiguration(period_in_ms=10000.5, points=[_SOME_POINT])
    decoded, factor = _decode_period(config.get_data())
    assert factor == 2
    assert decoded == 10000.5


def test_period_in_ms_round_trips_at_max_documented_value():
    # regression test: the period field stores period_in_ms * period_factor, not divided.
    # A previous fix mistakenly divided instead of multiplied, which silently produced a
    # much shorter real stimulation period than requested instead of the intended one.
    config = MidLevelChannelConfiguration(period_in_ms=_MAX_PERIOD_IN_MS, points=[_SOME_POINT])
    decoded, factor = _decode_period(config.get_data())
    assert factor == 2
    assert decoded == _MAX_PERIOD_IN_MS


@pytest.mark.parametrize("period_in_ms", [0.5, 0.75, 1, 2, 20, 100, 8191, 8192, 16383])
def test_period_in_ms_round_trips_exactly(period_in_ms):
    config = MidLevelChannelConfiguration(period_in_ms=period_in_ms, points=[_SOME_POINT])
    decoded, _ = _decode_period(config.get_data())
    assert decoded == period_in_ms


def test_get_data_raises_for_period_above_max():
    config = MidLevelChannelConfiguration(period_in_ms=_MAX_PERIOD_IN_MS + 1, points=[_SOME_POINT])
    with pytest.raises(ValueError):
        config.get_data()


def test_get_data_raises_for_negative_period():
    config = MidLevelChannelConfiguration(period_in_ms=-1, points=[_SOME_POINT])
    with pytest.raises(ValueError):
        config.get_data()


@pytest.mark.parametrize("period_in_ms", [0, 0.25, 0.49])
def test_get_data_raises_for_period_below_documented_minimum(period_in_ms):
    # datasheet: "Impulse repetition period: 0.5 - 16383 ms" -> 0 is not a valid period
    config = MidLevelChannelConfiguration(period_in_ms=period_in_ms, points=[_SOME_POINT])
    with pytest.raises(ValueError):
        config.get_data()


def test_get_data_raises_for_period_16383_5_even_though_raw_field_would_fit():
    # regression test: 32767 / 2 = 16383.5 fits in the 15 bit raw field and is within the
    # "1-32767" range the protocol documents for the raw value, but a real P24 rejects this
    # exact encoding with a Parameter error. Only up to 16383ms (raw=32766) is accepted.
    config = MidLevelChannelConfiguration(period_in_ms=16383.5, points=[_SOME_POINT])
    with pytest.raises(ValueError):
        config.get_data()
