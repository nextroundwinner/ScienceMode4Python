"""Provides device class representing a P24"""

from .device import Device, DeviceCapability
from .utils.connection import Connection
from .protocol.types import StimStatus
from .low_level.low_level_layer import LayerLowLevel
from .mid_level.mid_level_layer import LayerMidLevel


class DeviceP24(Device):
    """Device class for a P24 device"""

    def __init__(self, conn: Connection):
        super().__init__(conn, [DeviceCapability.LOW_LEVEL,
                                DeviceCapability.MID_LEVEL])

        self._layer_mid_level = LayerMidLevel(self._packet_buffer, self._packet_factory, self._packet_number_generator)
        self._layer_low_level = LayerLowLevel(self._packet_buffer, self._packet_factory, self._packet_number_generator)


    async def initialize(self):
        """Initialize device to get basic information (serial, versions) and stop any active stimulation/measurement"""
        # get stim status to see if low/mid level is initialized or running
        stim_status = await self.get_layer_general().get_stim_status()
        if stim_status.stim_status == StimStatus.LOW_LEVEL_INITIALIZED:
            await self.get_layer_low_level().stop()
        elif stim_status.stim_status in [StimStatus.MID_LEVEL_INITIALIZED, StimStatus.MID_LEVEL_RUNNING]:
            await self.get_layer_mid_level().stop()

        await super().initialize()


    def get_layer_mid_level(self) -> LayerMidLevel:
        """Helper function to access mid level layer"""
        return self._layer_mid_level


    def get_layer_low_level(self) -> LayerLowLevel:
        """Helper function to access low level layer"""
        return self._layer_low_level
