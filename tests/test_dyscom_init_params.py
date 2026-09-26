"""Tests for DyscomInitParams"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

import time

from science_mode_4.dyscom.dyscom_types import DyscomInitParams
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
