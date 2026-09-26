"""Tests for NullConnection"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

from science_mode_4.utils.null_connection import NullConnection


def test_null_connection_is_instantiable():
    # regression test: NullConnection used to override write()/read() directly instead
    # of implementing the abstract _read_intern()/clear_buffer() methods required by
    # Connection, so NullConnection() raised TypeError ("Can't instantiate abstract
    # class") and could never actually be used
    connection = NullConnection()
    assert connection is not None


def test_null_connection_open_close_tracks_state():
    connection = NullConnection()
    assert connection.is_open() is False

    connection.open()
    assert connection.is_open() is True

    connection.close()
    assert connection.is_open() is False


def test_null_connection_read_returns_empty_bytes():
    connection = NullConnection()
    connection.open()
    assert connection.read() == b""


def test_null_connection_write_and_clear_buffer_do_not_raise():
    connection = NullConnection()
    connection.open()
    connection.write(b"\x01\x02")
    connection.clear_buffer()
