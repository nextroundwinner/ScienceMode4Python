"""Provides class for ADS129x chip respiration control register"""

from dataclasses import dataclass
from enum import IntEnum


class Ads129xRespirationDemodulationCircuitry(IntEnum):
    """Represent ADS129xtype for respiration demodulation circuitry (respiration control register, 0x16)"""
    DEMODULATION_CIRCUITRY_OFF = 0
    DEMODULATION_CIRCUITRY_ON = 1


class Ads129xRespirationModulationCircuitry(IntEnum):
    """Represent ADS129xtype for respiration modulation circuitry (respiration control register, 0x16)"""
    MODULATION_CIRCUITRY_OFF = 0
    MODULATION_CIRCUITRY_ON = 1


class Ads129xRespirationPhase(IntEnum):
    """Represent ADS129xtype for respiration phase (respiration control register, 0x16)"""
    PHASE_22_5 = 0
    PHASE_45_0 = 1
    PHASE_67_5 = 2
    PHASE_90_0 = 3
    PHASE_112_5 = 4
    PHASE_135_0 = 5
    PHASE_157_5 = 6


class Ads129xRespirationControl(IntEnum):
    """Represent ADS129xtype for respiration control (respiration control register, 0x16)"""
    NO_RESPIRATION = 0
    EXTERNAL_RESPIRATION = 1
    INTERNAL_RESPIRATION_WITH_INTERNAL_SIGNAL = 2
    INTERNAL_RESPIRATION_WITH_USER_GENERATED_SIGNAL = 3


@dataclass
class Ads129xRespirationControlRegister:
    """Describes respiration control register of ADS129x chip"""

    respiration_demodulation_circuitry: Ads129xRespirationDemodulationCircuitry = \
        Ads129xRespirationDemodulationCircuitry.DEMODULATION_CIRCUITRY_ON
    respiration_modulation_circuitry: Ads129xRespirationModulationCircuitry = \
        Ads129xRespirationModulationCircuitry.MODULATION_CIRCUITRY_ON
    respiration_phase: Ads129xRespirationPhase = Ads129xRespirationPhase.PHASE_67_5
    respiration_control: Ads129xRespirationControl = Ads129xRespirationControl.INTERNAL_RESPIRATION_WITH_INTERNAL_SIGNAL


    def set_data(self, data: bytes):
        """Convert data to information"""
        tmp = data[0]
        self.respiration_demodulation_circuitry = Ads129xRespirationDemodulationCircuitry((tmp >> 7) & 0x01)
        self.respiration_modulation_circuitry = Ads129xRespirationModulationCircuitry((tmp >> 6) & 0x01)
        self.respiration_phase = Ads129xRespirationPhase((tmp >> 2) & 0x07)
        self.respiration_control = Ads129xRespirationControl((tmp >> 0) & 0x03)


    def get_data(self) -> bytes:
        """Convert information to bytes"""
        tmp = ((self.respiration_demodulation_circuitry << 7) |
               (self.respiration_modulation_circuitry << 6) | (1 << 5) |
               (self.respiration_phase << 2) | (self.respiration_control << 0))
        return [tmp]
