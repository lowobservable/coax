"""
coax.exceptions
~~~~~~~~~~~~~~~
"""

class InterfaceError(Exception):
    """An interface error occurred."""

class ReceiveError(Exception):
    """A receive error occurred."""

class InterfaceTimeout(Exception):
    """The interface timed out."""

class ReceiveTimeout(Exception):
    """The receive operation timed out."""

class ProtocolError(Exception):
    """A protocol error occurred."""
