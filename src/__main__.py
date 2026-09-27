"""Test program how to use library without installing the library,
DO NOT USE THIS FILE, USE EXAMPLES INSTEAD"""

import sys
import asyncio
import datetime

from science_mode_4.device_i24 import DeviceI24
from science_mode_4.dyscom.dyscom_types import DyscomFilterType, DyscomInitFlag, DyscomInitParams, DyscomPowerModulePowerType,\
    DyscomPowerModuleType, DyscomSignalType, DyscomSysType
from science_mode_4.utils.serial_port_connection import SerialPortConnection


async def main() -> int:
    """Main function"""

    # create serial port connection
    connection = SerialPortConnection(SerialPortConnection.list_science_mode_device_ports()[0].device)
    # open connection, now we can read and write data
    connection.open()

    # create science mode device
    device = DeviceI24(connection)
    # call initialize to get basic information (serial, versions) and stop any active stimulation/measurement
    # to have a defined state
    await device.initialize()


    # get dyscom layer to call low level commands
    dyscom = device.get_layer_dyscom()
    device_id = await dyscom.get_device_id()

    ####
    calibration_filename = f"rehaingest_{device_id}.cal"
    calibration_content = await dyscom.get_file_content(calibration_filename)
    print(f"Calibration content length: {len(calibration_content)}")
    calculated_checksum = (calibration_content[0] << 8) | calibration_content[1]
    print(f"Calculated calibration content checksum: {calculated_checksum}")

    ####
    file_info = await dyscom.get_file_info(calibration_filename)
    print(f"Calibration file info checksum: {file_info.checksum}")

    s_y_s = await dyscom.sys(DyscomSysType.DEVICE_STORAGE)
    print(f"Sys {s_y_s.state.name}")

    # call enable measurement power module and memory card for measurement
    await dyscom.power_module(DyscomPowerModuleType.MEASUREMENT, DyscomPowerModulePowerType.SWITCH_ON)
    await dyscom.power_module(DyscomPowerModuleType.MEMORY_CARD, DyscomPowerModulePowerType.SWITCH_ON)
    # call init with lowest sample rate (because of performance issues with plotting values)
    init_params = DyscomInitParams()
    init_params.signal_type = [DyscomSignalType.BI, DyscomSignalType.EMG_1]
    init_params.filter = DyscomFilterType.PREDEFINED_FILTER_1
    # we want no live data and write all data to memory card
    init_params.flags = [DyscomInitFlag.ENABLE_SD_STORAGE_MODE]
    # device stops recording at the minute boundary of start time + duration
    init_params.duration = datetime.timedelta(minutes=2)
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
    # close serial port connection
    connection.close()

    return 0


if __name__ == "__main__":
    res = asyncio.run(main())
    sys.exit(res)
