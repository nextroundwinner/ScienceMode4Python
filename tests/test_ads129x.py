"""Tests for Ads129x and its nested register dataclasses"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

from science_mode_4.dyscom.ads129x.ads129x import Ads129x
from science_mode_4.dyscom.ads129x.ads129x_config_register_1 import Ads129xPowerMode
from science_mode_4.dyscom.ads129x.ads129x_channel_settings_register import Ads129xChannelGain


def test_nested_registers_are_separate_instances_per_ads129x():
    # regression test: dataclass fields without a type annotation (e.g.
    # "config_register_1 = Ads129xConfigRegister1()") are not real dataclass fields,
    # they remain plain class attributes shared by every instance. Mutating one Ads129x's
    # nested register used to silently corrupt every other Ads129x instance's "own" register.
    a = Ads129x()
    b = Ads129x()

    assert a.config_register_1 is not b.config_register_1
    assert a.config_register_2 is not b.config_register_2
    assert a.config_register_3 is not b.config_register_3
    assert a.config_register_4 is not b.config_register_4
    assert a.channel_1_setting_register is not b.channel_1_setting_register
    assert a.channel_2_setting_register is not b.channel_2_setting_register
    assert a.channel_3_setting_register is not b.channel_3_setting_register
    assert a.channel_4_setting_register is not b.channel_4_setting_register
    assert a.respiration_control_register is not b.respiration_control_register


def test_mutating_one_instance_does_not_affect_another():
    a = Ads129x()
    b = Ads129x()

    a.config_register_1.power_mode = Ads129xPowerMode.LOW_POWER
    a.channel_1_setting_register.gain = Ads129xChannelGain.GAIN_12

    assert b.config_register_1.power_mode == Ads129xPowerMode.HIGH_RESOLUTION
    assert b.channel_1_setting_register.gain == Ads129xChannelGain.GAIN_6


def test_plain_int_fields_are_independent_per_instance():
    a = Ads129x()
    b = Ads129x()

    a.device_id = 42

    assert b.device_id == 0
