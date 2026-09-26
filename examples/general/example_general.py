"""Provides an example how to use general layer"""

import sys
import asyncio

from science_mode_4 import SerialPortConnection
from science_mode_4 import DeviceP24
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
        device = DeviceP24(connection)
        # call initialize to get basic information (serial, versions) and stop any active stimulation/measurement
        # to have a defined state
        await device.initialize()

        # get general layer to call general commands
        general = device.get_layer_general()
        print(f"Device id: {general.device_id}")
        print(f"Firmware version: {general.firmware_version}")
        print(f"Science mode version: {general.science_mode_version}")
    finally:
        # always close the serial port connection, even if an exception occurred above,
        # otherwise the COM port stays locked for subsequent runs
        if connection is not None:
            connection.close()

    return 0


if __name__ == "__main__":
    res = asyncio.run(main())
    sys.exit(res)
