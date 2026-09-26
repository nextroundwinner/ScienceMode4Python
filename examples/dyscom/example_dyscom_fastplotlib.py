"""Example how to use dyscom with fastplotlib for fast plotting of values.
Because fastplotlib requires its own event loop, we handle all device communication in a
background thread and synchronize measurement data vie Queue to main thread"""

import asyncio
import threading

import fastplotlib as fpl

from science_mode_4 import DeviceI24
from science_mode_4 import Commands
from science_mode_4 import SerialPortConnection
from science_mode_4.dyscom.ads129x.ads129x_config_register_1 import Ads129xOutputDataRate, Ads129xPowerMode
from science_mode_4.dyscom.dyscom_get_operation_mode import PacketDyscomGetAckOperationMode
from science_mode_4.dyscom.dyscom_send_live_data import PacketDyscomSendLiveData
from science_mode_4.dyscom.dyscom_types import DyscomGetType, DyscomInitParams, DyscomPowerModulePowerType,\
    DyscomPowerModuleType, DyscomSignalType
from science_mode_4.protocol.types import ResultAndError
from examples.utils.fastplotlib_utils import FastPlotLibHelper
from examples.utils.example_utils import ExampleUtils


def main():
    """Main function"""

    # initialize plot helper the handle plot specific things
    plot_helper = FastPlotLibHelper({0: ["Channel 1", "b"], 1: ["Channel 2", "r"], 2: ["Channel 3", "y"],\
                        3: ["Channel 4", "g"]}, 1000)
    # flag to indicate
    is_window_open: bool = True

    async def device_communication() -> int:
        """Communication with science mode device"""

        # get comport from command line argument
        com_port = ExampleUtils.get_comport_from_commandline_argument()

        connection = None
        try: # pylint:disable=too-many-nested-blocks
            # create serial port connection
            connection = SerialPortConnection(com_port)
            # open connection, now we can read and write data
            connection.open()

            # create science mode device
            device = DeviceI24(connection)
            # call initialize to get basic information (serial, versions) and stop any active stimulation/measurement
            # to have a defined state
            await device.initialize()

            # get dyscom layer to call dyscom level commands
            dyscom = device.get_layer_dyscom()

            # call enable measurement power module for measurement
            await dyscom.power_module(DyscomPowerModuleType.MEASUREMENT, DyscomPowerModulePowerType.SWITCH_ON)
            # call init with lowest sample rate and enable signal types
            init_params = DyscomInitParams()
            init_params.signal_type = [DyscomSignalType.BI, DyscomSignalType.EMG_1,\
                                    DyscomSignalType.EMG_2, DyscomSignalType.BREATHING]
            init_params.register_map_ads129x.config_register_1.output_data_rate = Ads129xOutputDataRate.HR_MODE_500_SPS__LP_MODE_250_SPS
            init_params.register_map_ads129x.config_register_1.power_mode = Ads129xPowerMode.LOW_POWER
            await dyscom.init(init_params)

            # start dyscom measurement
            await dyscom.start()

            # loop for some time
            for x in range(5000):
                # check if we closed window
                if not is_window_open:
                    break

                # check operation mode from time to time, this function is not waiting for response
                # so we have to handle it by ourself later
                if x % 500 == 0:
                    dyscom.send_get_operation_mode()

                live_data_counter = 0
                while True:
                    # process all available packages
                    ack = dyscom.packet_buffer.get_packet_from_buffer(live_data_counter == 0)
                    if ack:
                        # because there are multiple get commands, we need to additionally check kind,
                        # which is always associated DyscomGetType
                        if ack.command == Commands.DL_GET_ACK and ack.kind == DyscomGetType.OPERATION_MODE:
                            om_ack: PacketDyscomGetAckOperationMode = ack
                            print(f"Operation mode {om_ack.operation_mode.name}")
                            # check if measurement is still active
                            if om_ack.result_error != ResultAndError.NO_ERROR:
                                break
                        elif ack.command == Commands.DL_SEND_LIVE_DATA:
                            live_data_counter += 1

                            sld: PacketDyscomSendLiveData = ack
                            if sld.status_error:
                                print(f"SendLiveData status error {sld.samples}")
                                break

                            for x in range(4):
                                plot_helper.append_value(x, sld.samples[x].value)

                            plot_helper.update()
                    else:
                        # print(f"Live data acknowledges per iteration {live_data_counter}")
                        break

                await asyncio.sleep(0.001)

            # stop measurement
            await dyscom.stop()
            # turn power module off
            await dyscom.power_module(DyscomPowerModuleType.MEASUREMENT, DyscomPowerModulePowerType.SWITCH_OFF)
        finally:
            # always close the serial port connection, even if an exception occurred above,
            # otherwise the COM port stays locked for subsequent runs
            if connection is not None:
                connection.close()

        print("Close plot window to end example")

        return 0


    def data_generator() -> int:
        """Background function"""
        return asyncio.run(device_communication())


    # Create and start the data generator thread (aka background thread)
    data_thread = threading.Thread(target=data_generator, daemon=True)
    data_thread.start()

    # fastplotlib requires a main loop to draw everything
    fpl.loop.run()
    is_window_open = False


if __name__ == "__main__":
    main()
