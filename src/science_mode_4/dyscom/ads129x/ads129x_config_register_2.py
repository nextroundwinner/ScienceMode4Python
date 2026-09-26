"""Provides class for ADS129x chip config register 2"""

from dataclasses import dataclass
from enum import IntEnum


class Ads129xWctChoppingScheme(IntEnum):
    """Represent ADS129xtype for WCT chopping scheme (configuration register 2, 0x02)"""
    CHOPPING_FREQUENCY_VARIES = 0
    CHOPPING_FREQUENCY_CONSTANT = 1


class Ads129xTestSignalSource(IntEnum):
    """Represent ADS129xtype for test signal source (configuration register 2, 0x02)"""
    EXTERNAL_TEST_SIGNAL = 0
    INTERNAL_TEST_SIGNAL = 1


class Ads129xTestSignalAmplitude(IntEnum):
    """Represent ADS129xtype for test signal amplitude (configuration register 2, 0x02)"""
    SINGLE_VREF = 0
    DOUBLE_VREF = 1


class Ads129xTestSignalFrequency(IntEnum):
    """Represent ADS129xtype for test signal frequency (configuration register 2, 0x02)"""
    PULSE_AT_2_21 = 0
    PULSE_AT_2_20 = 1
    PULSE_AT_DC = 3


@dataclass
class Ads129xConfigRegister2:
    """Describes config register 2 of ADS129x chip"""

    wct_chopping_scheme: Ads129xWctChoppingScheme = Ads129xWctChoppingScheme.CHOPPING_FREQUENCY_VARIES
    test_signal_source: Ads129xTestSignalSource = Ads129xTestSignalSource.EXTERNAL_TEST_SIGNAL
    test_signal_amplitude: Ads129xTestSignalAmplitude = Ads129xTestSignalAmplitude.SINGLE_VREF
    test_signal_frequency: Ads129xTestSignalFrequency = Ads129xTestSignalFrequency.PULSE_AT_2_21


    def set_data(self, data: bytes):
        """Convert data to information"""
        tmp = data[0]
        self.wct_chopping_scheme = Ads129xWctChoppingScheme((tmp >> 5) & 0x01)
        self.test_signal_source = Ads129xTestSignalSource((tmp >> 4) & 0x01)
        self.test_signal_amplitude = Ads129xTestSignalAmplitude((tmp >> 2) & 0x01)
        self.test_signal_frequency = Ads129xTestSignalFrequency((tmp >> 0) & 0x03)


    def get_data(self) -> bytes:
        """Convert information to bytes"""
        tmp = ((self.wct_chopping_scheme << 5) | (self.test_signal_source << 4) |
               (self.test_signal_amplitude << 2) | (self.test_signal_frequency << 0))
        return [tmp]
