"""Tests for Ads129xConfigRegister3 and Ads129xConfigRegister4 bit decoding.
Bit positions verified against the official ADS1294/6/8(R) datasheet (SBAS459K),
Table 20 (CONFIG3, address 03h) and Table 33 (CONFIG4, address 17h)."""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

from science_mode_4.dyscom.ads129x.ads129x_config_register_3 import (
    Ads129xConfigRegister3,
    Ads129xPowerDownReferenceBuffer,
    Ads129xReferenceVoltage,
    Ads129xRldBufferPower,
    Ads129xRldLeadOffStatus,
    Ads129xRldMeasurement,
    Ads129xRldReferenceSignal,
    Ads129xRldSenseFunction,
)
from science_mode_4.dyscom.ads129x.ads129x_config_register_4 import (
    Ads129xConfigRegister4,
    Ads129xRespirationModulationFrequency,
)


def test_config_register_3_decodes_all_fields_from_distinct_bits():
    # regression test: rld_reference_signal used to read bit4 (duplicate of
    # rld_measurement) instead of bit3 (RLDREF_INT), and rld_buffer_power used to
    # read bit3 instead of bit2 (PD_RLD) - datasheet Table 20 bit layout:
    # 7=PD_REFBUF 6=reserved 5=VREF_4V 4=RLD_MEAS 3=RLDREF_INT 2=PD_RLD 1=RLD_LOFF_SENS 0=RLD_STAT
    reg = Ads129xConfigRegister3()
    reg.set_data([0b1_0_1_1_1_0_1_1])

    assert reg.power_down_reference_buffer == Ads129xPowerDownReferenceBuffer.ENABLE_INTERNAL_REFERENCE_BUFFER
    assert reg.reference_voltage == Ads129xReferenceVoltage.VREF_4_0
    assert reg.rld_measurement == Ads129xRldMeasurement.ROUTED
    assert reg.rld_reference_signal == Ads129xRldReferenceSignal.GENERATED_INTERNALLY
    assert reg.rld_buffer_power == Ads129xRldBufferPower.BUFFER_POWERED_DOWN
    assert reg.rld_sense_function == Ads129xRldSenseFunction.SENSE_ENABLED
    assert reg.rld_lead_off_status == Ads129xRldLeadOffStatus.DISCONNECTED


def test_config_register_3_rld_reference_signal_independent_of_rld_measurement():
    # with the bug, rld_reference_signal always mirrored rld_measurement since
    # both read the same bit
    reg = Ads129xConfigRegister3()
    reg.set_data([0b0_0_0_0_1_0_0_0])  # bit4 (RLD_MEAS)=0, bit3 (RLDREF_INT)=1
    assert reg.rld_measurement == Ads129xRldMeasurement.OPEN
    assert reg.rld_reference_signal == Ads129xRldReferenceSignal.GENERATED_INTERNALLY


def test_config_register_3_set_data_get_data_round_trip():
    reg = Ads129xConfigRegister3()
    reg.rld_reference_signal = Ads129xRldReferenceSignal.GENERATED_INTERNALLY
    reg.rld_buffer_power = Ads129xRldBufferPower.BUFFER_POWERED_DOWN

    decoded = Ads129xConfigRegister3()
    decoded.set_data(reg.get_data())

    assert decoded.rld_reference_signal == reg.rld_reference_signal
    assert decoded.rld_buffer_power == reg.rld_buffer_power


def test_config_register_4_decodes_full_3_bit_resp_freq_field():
    # regression test: mask was 0x08 instead of 0x07 for the 3 bit RESP_FREQ[2:0]
    # field at bits 7:5, so after ">> 5" only bits 0-2 can ever be nonzero and the
    # 0x08 mask always evaluated to 0 - respiration_modulation_frequency was stuck
    # at MODULATION_CLOCK_64KHZ (0) no matter what the device actually sent
    reg = Ads129xConfigRegister4()
    reg.set_data([0b111_00000])
    assert reg.respiration_modulation_frequency == Ads129xRespirationModulationFrequency.SQUARE_WAVE_500HZ

    reg.set_data([0b101_00000])
    assert reg.respiration_modulation_frequency == Ads129xRespirationModulationFrequency.SQUARE_WAVE_2KHZ

    reg.set_data([0b000_00000])
    assert reg.respiration_modulation_frequency == Ads129xRespirationModulationFrequency.MODULATION_CLOCK_64KHZ


def test_config_register_4_set_data_get_data_round_trip():
    reg = Ads129xConfigRegister4()
    reg.respiration_modulation_frequency = Ads129xRespirationModulationFrequency.SQUARE_WAVE_1KHZ

    decoded = Ads129xConfigRegister4()
    decoded.set_data(reg.get_data())

    assert decoded.respiration_modulation_frequency == reg.respiration_modulation_frequency
