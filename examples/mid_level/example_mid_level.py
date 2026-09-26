"""Provides an example how to use mid level layer"""

import sys
import asyncio

from science_mode_4 import DeviceP24
from science_mode_4 import MidLevelChannelConfiguration
from science_mode_4 import ChannelPoint
from science_mode_4 import SerialPortConnection
from examples.utils.example_utils import ExampleUtils, KeyboardInputThread


async def main() -> int:
    """Main function"""

    # keyboard is our trigger to end program
    def input_callback(input_value: str) -> bool:
        """Callback call from keyboard input thread"""
        # print(f"Input value {input_value}")

        if input_value == "q":
            # end keyboard input thread
            return True

        print("Invalid command")
        return False

    print("Usage: stimulation is running, press q to quit")
    # create keyboard input thread for non blocking console input
    keyboard_input_thread = KeyboardInputThread(input_callback)

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

        # simple stimulation pattern
        c1p1: ChannelPoint = ChannelPoint(200, 20)
        c1p2: ChannelPoint = ChannelPoint(100, 0)
        c1p3: ChannelPoint = ChannelPoint(200, -20)
        cc1 = MidLevelChannelConfiguration(True, 3, 20, [c1p1, c1p2, c1p3])

        c2p1: ChannelPoint = ChannelPoint(100, 10)
        c2p2: ChannelPoint = ChannelPoint(100, 0)
        c2p3: ChannelPoint = ChannelPoint(100, -10)
        cc2 = MidLevelChannelConfiguration(True, 3, 10, [c2p1, c2p2, c2p3])

        # get mid level layer to call mid level commands
        mid_level = device.get_layer_mid_level()
        # call init mid level, we want to stop on all stimulation errors
        await mid_level.init(True)
        # set stimulation pattern, P24 device will now stimulate according this pattern
        await mid_level.update([cc1, cc2])

        while keyboard_input_thread.is_alive():
            # we have to call get_current_data() every 1.5s to keep stimulation ongoing
            update = await mid_level.get_current_data() # pylint:disable=unused-variable
            # print(update)

            await asyncio.sleep(1)

        # call stop mid level
        await mid_level.stop()
    finally:
        # always close the serial port connection, even if an exception occurred above,
        # otherwise the COM port stays locked for subsequent runs
        if connection is not None:
            connection.close()

    return 0


if __name__ == "__main__":
    res = asyncio.run(main())
    sys.exit(res)
