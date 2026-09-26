"""Provides an example how to use dyscom level layer to read stored data from device"""

import asyncio

from science_mode_4 import DeviceI24
from science_mode_4 import SerialPortConnection
from science_mode_4.dyscom.dyscom_types import DyscomFilterType, DyscomInitFlag, DyscomInitParams, DyscomPowerModulePowerType,\
    DyscomPowerModuleType, DyscomSignalType
from examples.utils.example_utils import ExampleUtils


async def main() -> int:
    """Main function"""

    # get comport from command line argument
    com_port = ExampleUtils.get_comport_from_commandline_argument()

    connection = None
    try:
        # create serial port connection
        connection = SerialPortConnection(com_port)
        # open connection, now we can read and write data
        connection.open()

        # create science mode device
        device = DeviceI24(connection)
        # call initialize to get basic information (serial, versions) and stop any active stimulation/measurement
        # to have a defined state
        await device.initialize()

        # get dyscom layer to call low level commands
        dyscom = device.get_layer_dyscom()

        # call enable measurement power module and memory card for measurement
        await dyscom.power_module(DyscomPowerModuleType.MEASUREMENT, DyscomPowerModulePowerType.SWITCH_ON)
        await dyscom.power_module(DyscomPowerModuleType.MEMORY_CARD, DyscomPowerModulePowerType.SWITCH_ON)
        # call init with 1k sample rate
        init_params = DyscomInitParams()
        init_params.signal_type = [DyscomSignalType.BI, DyscomSignalType.EMG_1]
        init_params.filter = DyscomFilterType.PREDEFINED_FILTER_1
        # we want no live data and write all data to memory card
        init_params.flags = [DyscomInitFlag.ENABLE_SD_STORAGE_MODE]
        init_result = await dyscom.init(init_params)

        # start dyscom measurement
        await dyscom.start()

        # wait 10s to have some measurement data
        await asyncio.sleep(10)

        # stop measurement
        await dyscom.stop()
        # turn power module off
        await dyscom.power_module(DyscomPowerModuleType.MEASUREMENT, DyscomPowerModulePowerType.SWITCH_OFF)

        # get all meas data
        measurement = await dyscom.get_meas_file_content(init_result.measurement_file_id)
        print(f"Sample rate: {measurement[0].name}")
        for key, value in measurement[1].items():
            print(f"Signal type: {key.name}, sample count: {len(value)}")

        # turn memory card off
        await dyscom.power_module(DyscomPowerModuleType.MEMORY_CARD, DyscomPowerModulePowerType.SWITCH_OFF)
    finally:
        # always close the serial port connection, even if an exception occurred above,
        # otherwise the COM port stays locked for subsequent runs
        if connection is not None:
            connection.close()

    return 0


if __name__ == "__main__":
    asyncio.run(main())
