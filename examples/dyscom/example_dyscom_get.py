"""Provides an example how to use dyscom layer get commands"""

import sys
import asyncio

from science_mode_4 import SerialPortConnection
from science_mode_4 import DeviceI24
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

        # get general layer to access general commands
        general = device.get_layer_general()
        # get dyscom layer to access dyscom commands
        dyscom = device.get_layer_dyscom()

        #####
        # dyscom layer provides a get command for device id, it is redundant to general layer device id
        # both values should be identical
        device_id = await dyscom.get_device_id()
        print(f"Device id from general layer: {general.device_id}, from dyscom layer: {device_id}")

        #####
        # dyscom layer provides a get command for firmware version, it is redundant to general layer firmware verion
        # both values should be identical
        firmware_version = await dyscom.get_firmware_version()
        print(f"Firmware version from general layer: {general.firmware_version}, from dyscom layer: {firmware_version}")

        #####
        # get command for file system status
        file_system_status = await dyscom.get_file_system_status()
        print(file_system_status)

        # this is the default calibration filename
        calibration_filename = f"rehaingest_{device_id}.cal"
        ####
        # get calibration file content
        calibration_content = await dyscom.get_file_content(calibration_filename)
        print(f"Calibration content length: {len(calibration_content)}")
        # I24 devices calculates checksum from first 2 bytes of the file content
        calculated_checksum = (calibration_content[0] << 8) | calibration_content[1]
        print(f"Calculated calibration content checksum: {calculated_checksum}")

        ####
        # get file info for calibration file
        file_info = await dyscom.get_file_info(calibration_filename)
        print(f"Calibration file info checksum: {file_info.checksum}")
    finally:
        # always close the serial port connection, even if an exception occurred above,
        # otherwise the COM port stays locked for subsequent runs
        if connection is not None:
            connection.close()

    return 0


if __name__ == "__main__":
    res = asyncio.run(main())
    sys.exit(res)
