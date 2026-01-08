"""Provides an example how to use mid level layer"""

import sys
import asyncio
import threading

from science_mode_4 import DeviceP24
from science_mode_4 import MidLevelChannelConfiguration
from science_mode_4 import ChannelPoint
from science_mode_4 import SerialPortConnection
from science_mode_4 import ResultAndError
from examples.utils.example_utils import ExampleUtils, KeyboardInputThread


async def main() -> int:
    """Main function"""

    # lock is used to avoid interference of async functions of mid level layer
    # mid_level.update() and mid_level.get_current_data() may run at the same
    # time if a key is pressed at the moment when mid_level.get_current_data() is running
    # (because they run on different event loops)
    lock = threading.Lock()

    # some points
    p1: ChannelPoint = ChannelPoint(200, 20)
    p2: ChannelPoint = ChannelPoint(100, 0)
    p3: ChannelPoint = ChannelPoint(200, -20)
    # channel configuration
    # we want to ignore first and last two channels (just for demonstration purpose how to handle unused channels)
    # we need to pad list with None to achieve correct indices
    # [None, None, ChannelConfig, ChannelConfig, ChannelConfig, ChannelConfig]
    channel_config = [MidLevelChannelConfiguration(False, 3, 20, [p1, p2, p3]) for x in range(4)]
    channel_config.insert(0, None)
    channel_config.insert(0, None)

    # keyboard is our trigger to end program
    def input_callback(input_value: str) -> bool:
        """Callback call from keyboard input thread"""
        # print(f"Input value {input_value}")

        if input_value == "q":
            # end keyboard input thread
            return True
        if  "1" <= input_value <= "8":
            index = int(input_value) - 1
            # check if index is in range of channel_config
            if 0 <= index < len(channel_config):
                cc = channel_config[index]
                # check if index contains a ChannelConfiguration object
                if cc is not None:
                    # toggle active
                    cc.is_active = not cc.is_active
                    with lock:
                        asyncio.run(mid_level.update(channel_config))
                else:
                    print("Channel config is None")
            else:
                print("Invalid channel config index")

            return False


        print("Invalid command")
        return False

    print("Usage: press 1-8 to toggle channel, press q to quit")
    print("Only channels 3-6 have a channel configuration (see comments where configuration is created)")
    # create keyboard input thread for non blocking console input
    keyboard_input_thread = KeyboardInputThread(input_callback)

    # get comport from command line argument
    com_port = ExampleUtils.get_comport_from_commandline_argument()
    # create serial port connection
    connection = SerialPortConnection(com_port)
    # open connection, now we can read and write data
    connection.open()

    # create science mode device
    device = DeviceP24(connection)
    # call initialize to get basic information (serial, versions) and stop any active stimulation/measurement
    # to have a defined state
    await device.initialize()

    # get mid level layer to call mid level commands
    mid_level = device.get_layer_mid_level()
    # call init mid level, we do not want to stop on all stimulation errors to be able to
    # see errors during get_current_data
    await mid_level.init(False)
    # set stimulation pattern, P24 device will now stimulate according this pattern
    await mid_level.update(channel_config)

    possible_errors = [ResultAndError.ELECTRODE_ERROR, ResultAndError.PULSE_TIMEOUT_ERROR, ResultAndError.PULSE_LOW_CURRENT_ERROR]
    while keyboard_input_thread.is_alive():
        # we have to call get_current_data() every 1.5s to keep stimulation ongoing
        with lock:
            _, _, channel_error = await mid_level.get_current_data()
            if any(v in possible_errors for v in channel_error):
                print(f"Channel with error: {[(i, v.name) for i, v in enumerate(channel_error) if v != ResultAndError.NO_ERROR]}")

        await asyncio.sleep(1)

    # call stop mid level
    await mid_level.stop()

    # close serial port connection
    connection.close()
    return 0


if __name__ == "__main__":
    res = asyncio.run(main())
    sys.exit(res)
