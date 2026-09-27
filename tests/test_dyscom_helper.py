"""Tests for DyscomHelper"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

import datetime

import pytest
from science_mode_4.dyscom.dyscom_helper import DyscomHelper


def test_str_to_bytes_pads_short_value_with_zeros():
    result = DyscomHelper.str_to_bytes("abc", 6)
    assert result == b"abc\x00\x00\x00"


def test_str_to_bytes_accepts_value_using_all_but_last_byte():
    result = DyscomHelper.str_to_bytes("abcde", 6)
    assert result == b"abcde\x00"


def test_str_to_bytes_raises_instead_of_silently_truncating_too_long_value():
    # regression test: a value longer than byte_count - 1 used to be silently
    # cut off instead of raising, so e.g. a filename could get truncated to a
    # different, unintended file without any indication
    with pytest.raises(ValueError):
        DyscomHelper.str_to_bytes("abcdef", 6)


def test_str_to_bytes_raises_for_value_exactly_at_byte_count():
    # byte_count includes the mandatory null terminator, so a value of
    # length byte_count (with none left over for the terminator) must fail too
    with pytest.raises(ValueError):
        DyscomHelper.str_to_bytes("abcdefg", 7)


class _FixedDstTimezone(datetime.tzinfo):
    """Timezone with a fixed dst offset"""

    def __init__(self, dst: datetime.timedelta):
        self._dst = dst

    def utcoffset(self, dt):
        return datetime.timedelta(hours=1) + self._dst

    def dst(self, dt):
        return self._dst

    def tzname(self, dt):
        return "fixed_dst"


def test_datetime_to_bytes_dst_flag_is_0_for_naive_datetime():
    assert DyscomHelper.datetime_to_bytes(datetime.datetime(2026, 1, 15, 12, 0, 0))[1] == 0


def test_datetime_to_bytes_dst_flag_is_0_for_timezone_without_dst():
    # regression test: dst() returns timedelta(0) here, which was compared with int 0
    # (never equal), so the dst flag was wrongly set to 1
    dt = datetime.datetime(2026, 1, 15, 12, 0, 0, tzinfo=_FixedDstTimezone(datetime.timedelta(0)))
    assert DyscomHelper.datetime_to_bytes(dt)[1] == 0


def test_datetime_to_bytes_dst_flag_is_1_for_timezone_with_dst():
    dt = datetime.datetime(2026, 7, 15, 12, 0, 0, tzinfo=_FixedDstTimezone(datetime.timedelta(hours=1)))
    assert DyscomHelper.datetime_to_bytes(dt)[1] == 1
