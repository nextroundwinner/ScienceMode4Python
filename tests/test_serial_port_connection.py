"""Tests for SerialPortConnection reconnect logic"""
# pylint: disable=missing-function-docstring,protected-access
# test names are self-explanatory, docstrings would only restate them

from unittest.mock import MagicMock, PropertyMock

import pytest
import serial

from science_mode_4.utils.serial_port_connection import SerialPortConnection


def _make_connection_with_mock_serial() -> tuple[SerialPortConnection, MagicMock]:
    connection = SerialPortConnection("COM_TEST", error_timeout_in_s=0)
    mock_ser = MagicMock()
    connection._ser = mock_ser
    return connection, mock_ser


def test_read_intern_retries_reopen_until_it_succeeds_without_raising():
    # regression test: on a SerialException, _read_intern tries to close+reopen
    # the port and resend the last written data. If reopening itself failed, the
    # code used to swallow that failure and still call self.write() on the still-closed
    # port, raising a confusing PortNotOpenError instead of handling the transient
    # error internally. The device can drop out repeatedly (observed on a real P24),
    # so reopening must be retried until it succeeds instead of giving up after one try.
    connection, mock_ser = _make_connection_with_mock_serial()
    connection._last_written_data = b"\x01\x02"
    type(mock_ser).in_waiting = PropertyMock(side_effect=serial.SerialException("ClearCommError"))
    mock_ser.open.side_effect = [serial.SerialException("still disconnected"),
                                  serial.SerialException("still disconnected"), None]

    result = connection._read_intern()

    assert result == bytes()
    assert mock_ser.close.call_count == 3
    assert mock_ser.open.call_count == 3
    mock_ser.write.assert_called_once_with(b"\x01\x02")


def test_read_intern_gives_up_after_max_reopen_attempts():
    # regression test: reopening must not retry forever, otherwise a permanently
    # disconnected device would hang the caller indefinitely. After
    # _MAX_REOPEN_ATTEMPTS failures, the last error is raised instead of retrying again.
    connection, mock_ser = _make_connection_with_mock_serial()
    type(mock_ser).in_waiting = PropertyMock(side_effect=serial.SerialException("ClearCommError"))
    mock_ser.open.side_effect = serial.SerialException("still disconnected")

    with pytest.raises(serial.SerialException):
        connection._read_intern()

    assert mock_ser.close.call_count == SerialPortConnection._MAX_REOPEN_ATTEMPTS
    assert mock_ser.open.call_count == SerialPortConnection._MAX_REOPEN_ATTEMPTS
    mock_ser.write.assert_not_called()


def test_read_intern_resends_last_written_data_when_reopen_succeeds():
    connection, mock_ser = _make_connection_with_mock_serial()
    connection._last_written_data = b"\x01\x02"
    type(mock_ser).in_waiting = PropertyMock(side_effect=serial.SerialException("ClearCommError"))

    connection._read_intern()

    mock_ser.close.assert_called_once()
    mock_ser.open.assert_called_once()
    mock_ser.write.assert_called_once_with(b"\x01\x02")


def test_read_intern_returns_data_without_reconnect_on_success():
    connection, mock_ser = _make_connection_with_mock_serial()
    type(mock_ser).in_waiting = PropertyMock(return_value=3)
    mock_ser.read_all.return_value = b"\xaa\xbb\xcc"

    result = connection._read_intern()

    assert result == b"\xaa\xbb\xcc"
    mock_ser.close.assert_not_called()
    mock_ser.open.assert_not_called()
