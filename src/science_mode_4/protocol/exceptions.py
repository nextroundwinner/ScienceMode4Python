"""File with all library specific exception classes"""


class ScienceMode4Error(Exception):
    """Base class for all library specific exceptions"""


class ProtocolError(ScienceMode4Error):
    """Exception for protocol errors"""
