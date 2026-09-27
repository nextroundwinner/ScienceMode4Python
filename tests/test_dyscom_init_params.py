"""Tests for DyscomInitParams"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

import datetime
import time

import pytest
from science_mode_4.dyscom.dyscom_helper import DyscomHelper
from science_mode_4.dyscom.dyscom_types import DyscomFilterType, DyscomInitFlag, DyscomInitParams, DyscomSignalType
from science_mode_4.dyscom.ads129x.ads129x_config_register_1 import Ads129xPowerMode


def test_register_map_ads129x_is_separate_instance_per_params():
    # regression test: "register_map_ads129x = Ads129x()" without a type annotation is
    # not a real dataclass field, so every DyscomInitParams instance shared the exact
    # same Ads129x object - mutating one caller's register map corrupted every other one
    a = DyscomInitParams()
    b = DyscomInitParams()

    assert a.register_map_ads129x is not b.register_map_ads129x

    a.register_map_ads129x.config_register_1.power_mode = Ads129xPowerMode.LOW_POWER
    assert b.register_map_ads129x.config_register_1.power_mode == Ads129xPowerMode.HIGH_RESOLUTION


def test_start_time_is_set_per_instance_not_frozen_at_import():
    # regression test: "start_time = datetime.datetime.now()" as a plain class-level
    # default is evaluated once when the module is imported, not per instance, so every
    # DyscomInitParams ever created got the same (increasingly stale) start_time
    a = DyscomInitParams()
    time.sleep(0.01)
    b = DyscomInitParams()

    assert a.start_time != b.start_time
    assert b.start_time > a.start_time


def test_signal_type_defaults_are_independent_lists():
    a = DyscomInitParams()
    b = DyscomInitParams()

    a.signal_type.append(a.signal_type[0])
    assert len(b.signal_type) == 2


def test_set_data_is_inverse_of_get_data():
    # regression test: set_data() was an empty stub, so e.g. the init params of a
    # received measurement meta info packet were always silently left at their defaults
    source = DyscomInitParams()
    source.register_map_ads129x.config_register_1.power_mode = Ads129xPowerMode.LOW_POWER
    source.start_time = datetime.datetime(2025, 3, 4, 5, 6, 7)
    source.system_time = datetime.datetime(2024, 12, 31, 23, 59, 58)
    source.proband_name = "proband"
    source.investigator_name = "investigator"
    source.proband_number = "42"
    source.duration = datetime.timedelta(seconds=3600)
    source.signal_type = [DyscomSignalType.EMG_1, DyscomSignalType.EMG_2, DyscomSignalType.BREATHING]
    source.sync_signal = True
    source.filter = DyscomFilterType.PREDEFINED_FILTER_2
    source.flags = {DyscomInitFlag.ENABLE_SD_STORAGE_MODE, DyscomInitFlag.MUTE}

    target = DyscomInitParams()
    target.set_data(source.get_data())

    assert target == source


def test_bytes_to_datetime_is_inverse_of_datetime_to_bytes():
    # regression test: bytes_to_datetime() unpacked year and day of year as little endian
    # while datetime_to_bytes() writes them big endian, e.g. year 2025 was read as 33900
    dt = datetime.datetime(2025, 3, 4, 5, 6, 7)
    assert DyscomHelper.bytes_to_datetime(DyscomHelper.datetime_to_bytes(dt)) == dt


def test_datetime_to_bytes_encodes_full_year_big_endian():
    # regression test: the year was sent as years since 1900 (126 for 2026), but the
    # I24 expects the full year - verified on a real device, which then set its clock
    # to year 2014 instead of 2026
    data = DyscomHelper.datetime_to_bytes(datetime.datetime(2026, 9, 26, 23, 41, 35))
    assert data[9:11] == (2026).to_bytes(2, "big")
    # day of year (0 based) is big endian as well
    assert data[7:9] == (268).to_bytes(2, "big")


def _encoded_duration(params: DyscomInitParams) -> int:
    # duration is located after register map (26), start/system time (2 * 11), proband/investigator
    # name (2 * 129), proband number (37) and signal type count (2)
    offset = 26 + 2 * 11 + 2 * 129 + 37 + 2
    return int.from_bytes(params.get_data()[offset:offset + 4], "big")


def test_duration_includes_days():
    # regression test: timedelta.seconds is only the seconds part without days,
    # so a duration of 1 day + 5 seconds was encoded as 5 seconds
    params = DyscomInitParams()
    params.duration = datetime.timedelta(days=1, seconds=5)
    assert _encoded_duration(params) == 86405


def test_negative_duration_raises():
    params = DyscomInitParams()
    params.duration = datetime.timedelta(seconds=-1)
    with pytest.raises(ValueError):
        params.get_data()
