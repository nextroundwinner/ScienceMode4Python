"""Provides device class representing a I24"""

from .device import Device, DeviceCapability
from .utils.connection import Connection
from .dyscom.dyscom_types import DyscomGetOperationModeType
from .dyscom.dyscom_layer import LayerDyscom


class DeviceI24(Device):
    """Device class for a I24 device"""

    def __init__(self, conn: Connection):
        super().__init__(conn, [DeviceCapability.DYSCOM])

        self._layer_dyscom = LayerDyscom(self._packet_buffer, self._packet_factory, self._packet_number_generator)


    async def initialize(self):
        """Initialize device to get basic information (serial, versions) and stop any active stimulation/measurement"""
        # get operation mode to see if dyscom measurement is running
        operation_mode = await self.get_layer_dyscom().get_operation_mode()
        if operation_mode in [DyscomGetOperationModeType.UNDEFINED,
                                DyscomGetOperationModeType.LIVE_MEASURING_PRE,
                                DyscomGetOperationModeType.LIVE_MEASURING,
                                DyscomGetOperationModeType.RECORD_PRE,
                                DyscomGetOperationModeType.RECORD,
                                DyscomGetOperationModeType.DATATRANSFER_PRE,
                                DyscomGetOperationModeType.DATATRANSFER]:
            await self.get_layer_dyscom().stop()

        await super().initialize()


    def get_layer_dyscom(self) -> LayerDyscom:
        """Helper function to access dyscom layer"""
        return self._layer_dyscom
