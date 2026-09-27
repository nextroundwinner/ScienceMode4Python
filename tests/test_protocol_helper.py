"""Tests for ProtocolHelper.send_packet_and_wait"""
# pylint: disable=missing-function-docstring,protected-access
# test names are self-explanatory, docstrings would only restate them

import asyncio
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from science_mode_4.protocol import protocol_helper as protocol_helper_module
from science_mode_4.protocol.commands import Commands
from science_mode_4.protocol.exceptions import ProtocolError
from science_mode_4.protocol.protocol_helper import ProtocolHelper


def _fake_ack(command: int, number: int):
    return SimpleNamespace(command=command, number=number)


def _make_request_packet(command: int, number: int):
    return SimpleNamespace(command=command, number=number, get_data=lambda: b"")


def test_stale_acks_are_drained_without_sleeping_between_them():
    # regression test: the inner loop used to unconditionally "break" after
    # inspecting a single packet, even when it was discarded as stale/mismatched,
    # so each stale ack cost a full asyncio.sleep(0.01) cycle before the buffer was
    # checked again. Multiple queued stale acks should now be drained in one pass,
    # with no sleep needed as long as the matching ack is already available.
    request = _make_request_packet(command=10, number=3)
    matching_ack = _fake_ack(command=11, number=3)

    packet_buffer = MagicMock()
    packet_buffer.get_packet_from_buffer.side_effect = [
        _fake_ack(command=99, number=3),   # stale: wrong command
        _fake_ack(command=11, number=7),   # stale: wrong number
        matching_ack,
    ]

    with patch("science_mode_4.protocol.protocol_helper.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = asyncio.run(ProtocolHelper.send_packet_and_wait(request, request.number, packet_buffer))

    assert result is matching_ack
    assert packet_buffer.get_packet_from_buffer.call_count == 3
    mock_sleep.assert_not_called()


def test_general_error_ack_raises_immediately():
    request = _make_request_packet(command=10, number=1)
    error_ack = SimpleNamespace(command=Commands.GENERAL_ERROR, number=1,
                                 result_error=SimpleNamespace(name="PARAMETER_ERROR"))

    packet_buffer = MagicMock()
    packet_buffer.get_packet_from_buffer.side_effect = [error_ack]

    with patch("science_mode_4.protocol.protocol_helper.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ProtocolError):
            asyncio.run(ProtocolHelper.send_packet_and_wait(request, request.number, packet_buffer))

    # regression test: waiting is aborted, so the acknowledge must no longer be counted as open
    packet_buffer.remove_open_acknowledge.assert_called_once_with(request)


def test_unknown_command_ack_raises_immediately_and_removes_open_acknowledge():
    request = _make_request_packet(command=10, number=1)
    error_ack = SimpleNamespace(command=Commands.UNKNOWN_COMMAND, number=1,
                                result_error=SimpleNamespace(name="INVALID_CMD_ERROR"))

    packet_buffer = MagicMock()
    packet_buffer.get_packet_from_buffer.side_effect = [error_ack]

    with patch("science_mode_4.protocol.protocol_helper.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ProtocolError):
            asyncio.run(ProtocolHelper.send_packet_and_wait(request, request.number, packet_buffer))

    packet_buffer.remove_open_acknowledge.assert_called_once_with(request)


def test_no_ack_available_still_sleeps_and_eventually_times_out():
    request = _make_request_packet(command=10, number=1)

    packet_buffer = MagicMock()
    packet_buffer.get_packet_from_buffer.return_value = None

    with patch("science_mode_4.protocol.protocol_helper.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(ProtocolError):
            asyncio.run(ProtocolHelper.send_packet_and_wait(
                request, request.number, packet_buffer, timeout_in_seconds=0.03))

    assert mock_sleep.call_count > 0
    packet_buffer.remove_open_acknowledge.assert_called_once_with(request)


def test_timeout_duration_matches_requested_timeout():
    # regression test: the timeout was implemented by counting sleep cycles, but asyncio.sleep(0.01)
    # sleeps longer than requested (~15.6 ms on Windows), so a 1 s timeout took ~1.55 s
    request = _make_request_packet(command=10, number=1)
    packet_buffer = MagicMock()
    packet_buffer.get_packet_from_buffer.return_value = None

    start = time.monotonic()
    with pytest.raises(ProtocolError):
        asyncio.run(ProtocolHelper.send_packet_and_wait(request, request.number, packet_buffer, timeout_in_seconds=0.3))
    elapsed = time.monotonic() - start

    assert 0.3 <= elapsed < 0.4


def test_ack_available_after_sleep_crossing_deadline_is_accepted():
    # the deadline is checked only after the buffer was processed, so an acknowledge
    # that arrived during the last sleep is not discarded
    request = _make_request_packet(command=10, number=3)
    matching_ack = _fake_ack(command=11, number=3)
    packet_buffer = MagicMock()
    packet_buffer.get_packet_from_buffer.side_effect = [None, matching_ack]

    now = [0.0]
    async def sleep_past_deadline(_duration):
        now[0] += 10.0

    with patch.object(protocol_helper_module, "time", SimpleNamespace(monotonic=lambda: now[0])), \
         patch("science_mode_4.protocol.protocol_helper.asyncio.sleep", side_effect=sleep_past_deadline):
        result = asyncio.run(ProtocolHelper.send_packet_and_wait(request, request.number, packet_buffer, timeout_in_seconds=1))

    assert result is matching_ack


def test_timeout_error_message_contains_command_name():
    request = _make_request_packet(command=Commands.GET_DEVICE_ID, number=1)
    packet_buffer = MagicMock()
    packet_buffer.get_packet_from_buffer.return_value = None

    with patch("science_mode_4.protocol.protocol_helper.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ProtocolError, match="GET_DEVICE_ID"):
            asyncio.run(ProtocolHelper.send_packet_and_wait(request, request.number, packet_buffer, timeout_in_seconds=0.02))


def test_timeout_error_message_contains_number_of_unknown_command():
    request = _make_request_packet(command=76, number=1)
    packet_buffer = MagicMock()
    packet_buffer.get_packet_from_buffer.return_value = None

    with patch("science_mode_4.protocol.protocol_helper.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ProtocolError, match="packet 76 "):
            asyncio.run(ProtocolHelper.send_packet_and_wait(request, request.number, packet_buffer, timeout_in_seconds=0.02))
