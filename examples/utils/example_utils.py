"""Provides some helper functionality for examples"""

import sys
import threading
import os
import asyncio
from typing import Callable
from getch import getch

from science_mode_4 import SerialPortConnection


class KeyboardInputThread(threading.Thread):
    """Thread for non blocking keyboard input"""

    def __init__(self, input_cbk: Callable[[str], bool]):
        self._input_cbk = input_cbk
        self._stop_requested = threading.Event()
        super().__init__(name = "keyboard_input_thread", daemon = True)
        self.start()


    def stop(self):
        """Requests the thread to end, e.g. after an exception elsewhere so it doesn't
        keep waiting for keyboard input that no longer matters.
        Note: getch() blocks until a key is pressed, so this can only take effect on
        the next keypress, not interrupt an already-blocked call. The thread is a
        daemon thread regardless, so it never prevents the process itself from exiting."""
        self._stop_requested.set()


    def run(self):
        while not self._stop_requested.is_set():
            # getch() returns a bytes object
            key_raw = getch()
            if self._stop_requested.is_set():
                break

            if os.name == "nt":
                key = bytes.decode(key_raw)
            else:
                key = key_raw
            # handle ctrl+c
            if key == "\x03":
                raise KeyboardInterrupt

            if self._input_cbk(key):
                # callback returned True, so end thread
                break


class ExampleUtils():
    """Helper functions for examples"""

    @staticmethod
    def get_comport_from_commandline_argument() -> str:
        """Get com port from command line argument, if no argument provided,
        look for the first matching device,
        if nothing found, end program with exit code 1"""
        if len(sys.argv) != 2:
            # check for available science mode device ports
            ports = SerialPortConnection.list_science_mode_device_ports()
            if len(ports) > 0:
                return ports[0].device

            # nothing found -> exit
            print("No science mode device found")
            print("Serial port command line argument missing (e.g. python -m examples.<layer>.<example> COM3)")
            sys.exit(1)

        com_port = sys.argv[1]
        return com_port


    @staticmethod
    async def wait_for_any_key_pressed(cb: Callable[[], None] | None):
        """Helper function to wait for any key press"""

        # keyboard func
        def input_callback(_input_value: str) -> bool:
            """Callback call from keyboard input thread"""
            # quit on any key
            return True

        # create keyboard input thread for non blocking console input
        keyboard_input_thread = KeyboardInputThread(input_callback)

        # now we can start stimulation
        while keyboard_input_thread.is_alive():
            if cb is not None:
                cb()
            await asyncio.sleep(0.1)
