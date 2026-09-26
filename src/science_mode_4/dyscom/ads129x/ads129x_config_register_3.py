"""Provides class for ADS129x chip config register 3"""

from dataclasses import dataclass
from enum import IntEnum


class Ads129xPowerDownReferenceBuffer(IntEnum):
    """Represent ADS129xtype for power down reference buffer (configuration register 3, 0x03)"""
    DISABLE_INTERNAL_REFERENCE_BUFFER = 0
    ENABLE_INTERNAL_REFERENCE_BUFFER = 1


class Ads129xReferenceVoltage(IntEnum):
    """Represent ADS129xtype for reference voltage (configuration register 3, 0x03)"""
    VREF_2_4 = 0
    VREF_4_0 = 1


class Ads129xRldMeasurement(IntEnum):
    """Represent ADS129xtype for RLD measurement (configuration register 3, 0x03)"""
    OPEN = 0
    ROUTED = 1


class Ads129xRldReferenceSignal(IntEnum):
    """Represent ADS129xtype for RLD reference signal (configuration register 3, 0x03)"""
    GENERATED_EXTERNALLY = 0
    GENERATED_INTERNALLY = 1


class Ads129xRldBufferPower(IntEnum):
    """Represent ADS129xtype for RLD buffer power (configuration register 3, 0x03)"""
    BUFFER_POWERED_DOWN = 0
    BUFFER_ENABLED = 1


class Ads129xRldSenseFunction(IntEnum):
    """Represent ADS129xtype for RLD sense function (configuration register 3, 0x03)"""
    SENSE_DISABLED = 0
    SENSE_ENABLED = 1


class Ads129xRldLeadOffStatus(IntEnum):
    """Represent ADS129xtype for RLD lead off status (configuration register 3, 0x03)"""
    CONNECTED = 0
    DISCONNECTED = 1


@dataclass
class Ads129xConfigRegister3:
    """Describes config register 3 of ADS129x chip"""

    power_down_reference_buffer: Ads129xPowerDownReferenceBuffer = Ads129xPowerDownReferenceBuffer.ENABLE_INTERNAL_REFERENCE_BUFFER
    reference_voltage: Ads129xReferenceVoltage = Ads129xReferenceVoltage.VREF_4_0
    rld_measurement: Ads129xRldMeasurement = Ads129xRldMeasurement.ROUTED
    rld_reference_signal: Ads129xRldReferenceSignal = Ads129xRldReferenceSignal.GENERATED_INTERNALLY
    rld_buffer_power: Ads129xRldBufferPower = Ads129xRldBufferPower.BUFFER_ENABLED
    rld_sense_function: Ads129xRldSenseFunction = Ads129xRldSenseFunction.SENSE_DISABLED
    rld_lead_off_status: Ads129xRldLeadOffStatus = Ads129xRldLeadOffStatus.CONNECTED


    def set_data(self, data: bytes):
        """Convert data to information"""
        tmp = data[0]
        self.power_down_reference_buffer = Ads129xPowerDownReferenceBuffer((tmp >> 7) & 0x01)
        self.reference_voltage = Ads129xReferenceVoltage((tmp >> 5) & 0x01)
        self.rld_measurement = Ads129xRldMeasurement((tmp >> 4) & 0x01)
        # CONFIG3 (datasheet Table 20): bit3 = RLDREF_INT, bit2 = PD_RLD
        self.rld_reference_signal = Ads129xRldReferenceSignal((tmp >> 3) & 0x01)
        self.rld_buffer_power = Ads129xRldBufferPower((tmp >> 2) & 0x01)
        self.rld_sense_function = Ads129xRldSenseFunction((tmp >> 1) & 0x01)
        self.rld_lead_off_status = Ads129xRldLeadOffStatus((tmp >> 0) & 0x01)


    def get_data(self) -> bytes:
        """Convert information to bytes"""
        tmp = ((self.power_down_reference_buffer << 7) | (1 << 6) |
               (self.reference_voltage << 5) |(self.rld_measurement << 4) |
               (self.rld_reference_signal << 3) | (self.rld_buffer_power << 2) |
               (self.rld_sense_function << 1) | (self.rld_lead_off_status << 0))
        return [tmp]
