"""Provides an example how to use dyscom level layer to measure emg and bi and plot values"""

import asyncio

from science_mode_4 import DeviceI24
from science_mode_4 import Commands
from science_mode_4 import SerialPortConnection
from science_mode_4.dyscom.ads129x.ads129x_config_register_1 import Ads129xOutputDataRate, Ads129xPowerMode
from science_mode_4.dyscom.dyscom_get_operation_mode import PacketDyscomGetAckOperationMode
from science_mode_4.dyscom.dyscom_send_live_data import PacketDyscomSendLiveData
from science_mode_4.dyscom.dyscom_types import DyscomInitParams, DyscomPowerModulePowerType, DyscomPowerModuleType, DyscomSignalType
from science_mode_4.utils.logger import logger
from examples.utils.example_utils import ExampleUtils
from examples.utils.pyplot_utils import PyPlotHelper


async def main() -> int:
    """Main function"""

    plot_helper = PyPlotHelper({0: ["BI", "blue"]}, 250)
    # disable logger to increase performance
    logger().disabled = True

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

        # get dyscom layer to call low level commands
        dyscom = device.get_layer_dyscom()

        # call enable measurement power module for measurement
        await dyscom.power_module(DyscomPowerModuleType.MEASUREMENT, DyscomPowerModulePowerType.SWITCH_ON)
        # call init with lowest sample rate (because of performance issues with plotting values)
        init_params = DyscomInitParams()
        init_params.signal_type = [DyscomSignalType.BI]
        init_params.register_map_ads129x.config_register_1.output_data_rate = Ads129xOutputDataRate.HR_MODE_500_SPS__LP_MODE_250_SPS
        init_params.register_map_ads129x.config_register_1.power_mode = Ads129xPowerMode.LOW_POWER
        await dyscom.init(init_params)

        # start dyscom measurement
        await dyscom.start()

        # loop for some time
        for x in range(5000):
            # check operation mode from time to time
            if x % 500 == 0:
                dyscom.send_get_operation_mode()

            live_data_counter = 0
            while True:
                ack = dyscom.packet_buffer.get_packet_from_buffer(live_data_counter == 0)
                if ack:
                    if ack.command == Commands.DL_GET_ACK:
                        om_ack: PacketDyscomGetAckOperationMode = ack
                        print(f"Operation mode {om_ack.operation_mode.name}")
                    elif ack.command == Commands.DL_SEND_LIVE_DATA:
                        live_data_counter += 1

                        sld: PacketDyscomSendLiveData = ack
                        if sld.status_error:
                            print(f"SendLiveData status error {sld.samples}")
                            break

                        # reduce framerate further
                        if sld.number % 60 == 0:
                            plot_helper.append_value(0, sld.samples[0].value)
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

    print("Close plot window to quit")
    plot_helper.loop()
    return 0


if __name__ == "__main__":
    asyncio.run(main())
