"""Provides a class for a usb connection"""

import libusb_package
import usb.core
import usb.util
from .connection import Connection

class UsbConnection(Connection):
    """USB connection class,
    IMPORTANT: work in progress (there are driver issues under windows)"""


    @staticmethod
    def list_devices() -> list[usb.core.Device]:
        """Returns all USB devices"""
        # return list(usb.core.find(find_all=True))
        return libusb_package.find(find_all=True)


    @staticmethod
    def list_science_mode_devices() -> list[usb.core.Device]:
        """Returns all potential science mode USB devices"""
        devices = UsbConnection.list_devices()
        # science mode devices (P24/I24) have an STM32 mcu and these are
        # default values for USB CDC devices
        filtered_devices = list(filter(lambda x: x.idVendor == 0x0483 and x.idProduct == 0x5740 and
                                       x.bDeviceClass == 0x02, devices))
        return filtered_devices


    def __init__(self, device: usb.core.Device):
        self._device = device
        self._out_endpoint: usb.core.Endpoint = None
        self._in_endpoint: usb.core.Endpoint = None
        self._in_endpoint_buffer_size = 128 * 64
        self._is_open = False


    def open(self):
        # P24/I24 have only one configuration
        self._device.set_configuration()
        # get an endpoint instance
        cfg = self._device.get_active_configuration()
        # Interface 0: CDC Communication
        # Interface 1: CDC Data
        interface: usb.core.Interface = cfg[(1,0)]

        # match the first OUT endpoint
        self._out_endpoint = usb.util.find_descriptor(
            interface,
            custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
        # match the first IN endpoint
        self._in_endpoint = usb.util.find_descriptor(
            interface,
            custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)

        self._is_open = True


    def close(self):
        # release the claimed interface/endpoints, otherwise a later open() (in this
        # process or another) can fail to claim the interface ("Resource busy")
        usb.util.dispose_resources(self._device)
        self._out_endpoint = None
        self._in_endpoint = None
        self._is_open = False


    def is_open(self) -> bool:
        return self._is_open


    def write(self, data: bytes):
        super().write(data)
        self._out_endpoint.write(data)


    def clear_buffer(self):
        # there is no way to clear the buffer from in endpoint, so
        # read all data and discard it
        self._read_intern()


    def _read_intern(self) -> bytes:
        data = bytes()
        try:
            while True:
                # Read up to endpoint's max packet size (64 bytes in this case)
                tmp = self._in_endpoint.read(self._in_endpoint_buffer_size)
                data += bytes(tmp)
                if len(tmp) < self._in_endpoint_buffer_size:
                    break
        except usb.core.USBError as e:
            if e.errno == 10060:
                # Timeout error (no data available)
                pass
            else:
                raise

        return data
