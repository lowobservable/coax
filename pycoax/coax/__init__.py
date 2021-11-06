from .__about__ import __version__

from .interface import InterfaceFeature
from .serial_interface import SerialInterface, open_serial_interface

from .protocol import (
    PollAction,
    PollResponse,
    PowerOnResetCompletePollResponse,
    KeystrokePollResponse,
    TerminalType,
    Control,
    SecondaryControl,
    Poll,
    PollAck,
    ReadStatus,
    ReadTerminalId,
    ReadExtendedId,
    ReadAddressCounterHi,
    ReadAddressCounterLo,
    ReadData,
    ReadMultiple,
    Reset,
    LoadControlRegister,
    LoadSecondaryControl,
    LoadMask,
    LoadAddressCounterHi,
    LoadAddressCounterLo,
    WriteData,
    Clear,
    SearchForward,
    SearchBackward,
    InsertByte,
    StartOperation,
    DiagnosticReset,
    ReadFeatureId,
    EABReadData,
    EABLoadMask,
    EABWriteAlternate,
    EABReadMultiple,
    EABWriteUnderMask,
    EABReadStatus,
    Data
)

from .features import (
    Feature,
    read_feature_ids,
    parse_features
)

from .multiplexer import get_device_address

from .exceptions import (
    InterfaceError,
    ReceiveError,
    InterfaceTimeout,
    ReceiveTimeout,
    ProtocolError
)
