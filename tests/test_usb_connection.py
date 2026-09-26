"""Tests for UsbConnection"""
# pylint: disable=missing-function-docstring,protected-access
# test names are self-explanatory, docstrings would only restate them

from unittest.mock import MagicMock, patch

from science_mode_4.utils.usb_connection import UsbConnection


def test_close_disposes_usb_resources_and_resets_state():
    # regression test: close() used to only flip _is_open to False without releasing
    # the claimed USB interface/endpoints, so a later open() (in this process or
    # another) could fail to claim the interface ("Resource busy")
    device = MagicMock()
    connection = UsbConnection(device)
    connection._out_endpoint = MagicMock()
    connection._in_endpoint = MagicMock()
    connection._is_open = True

    with patch("science_mode_4.utils.usb_connection.usb.util.dispose_resources") as mock_dispose:
        connection.close()

    mock_dispose.assert_called_once_with(device)
    assert connection._out_endpoint is None
    assert connection._in_endpoint is None
    assert connection.is_open() is False
