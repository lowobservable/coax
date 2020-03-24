import unittest
from unittest.mock import Mock
import sliplib

import context

from coax import SerialInterface, InterfaceError, ReceiveError, ReceiveTimeout

class SerialInterfaceResetTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = Mock()

        self.serial.timeout = None

        self.interface = SerialInterface(self.serial)

        self.interface._write_message = Mock()
        self.interface._read_message = Mock(return_value=bytes.fromhex('01 01 02 03'))

    def test_message_is_sent(self):
        # Act
        self.interface.reset()

        # Assert
        self.interface._write_message.assert_called_with(bytes.fromhex('01'))

    def test_version_is_formatted_correctly(self):
        self.assertEqual(self.interface.reset(), '1.2.3')

    def test_timeout_is_restored_after_reset(self):
        # Arrange
        self.serial.timeout = 123

        # Act
        self.interface.reset()

        # Assert
        self.assertEqual(self.serial.timeout, 123)

    def test_invalid_message_length_is_handled_correctly(self):
        # Arrange
        self.interface._read_message = Mock(return_value=bytes.fromhex('01 01'))

        # Act and assert
        with self.assertRaisesRegex(InterfaceError, 'Invalid reset response'):
            self.interface.reset()

    def test_error_is_handled_correctly(self):
        # Arrange
        self.interface._read_message = Mock(return_value=bytes.fromhex('02 01'))

        # Act and assert
        with self.assertRaisesRegex(InterfaceError, 'Invalid request message'):
            self.interface.reset()

# TODO...

class SerialInterfaceReadMessageTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = Mock()

        self.interface = SerialInterface(self.serial)

        self.interface.slip_serial = Mock()

    def test(self):
        # Arrange
        self.interface.slip_serial.recv_msg = Mock(return_value=bytes.fromhex('00 04 01 02 03 04 00 00'))

        # Act
        message = self.interface._read_message()

        # Assert
        self.assertEqual(message, bytes.fromhex('01 02 03 04'))

    def test_protocol_error_is_handled_correctly(self):
        # Arrange
        self.interface.slip_serial.recv_msg = Mock(side_effect=sliplib.ProtocolError)

        # Act and assert
        with self.assertRaisesRegex(InterfaceError, 'SLIP protocol error'):
            self.interface._read_message()

    def test_invalid_message_length_is_handled_correctly(self):
        # Arrange
        self.interface.slip_serial.recv_msg = Mock(return_value=bytes.fromhex('00'))

        # Act and assert
        with self.assertRaisesRegex(InterfaceError, 'Invalid response message'):
            self.interface._read_message()

    def test_message_length_mismatch_is_handled_correctly(self):
        # Arrange
        self.interface.slip_serial.recv_msg = Mock(return_value=bytes.fromhex('00 05 01 02 03 04 00 00'))

        # Act and assert
        with self.assertRaisesRegex(InterfaceError, 'Response message length mismatch'):
            self.interface._read_message()

    def test_empty_message_is_handled_correctly(self):
        # Arrange
        self.interface.slip_serial.recv_msg = Mock(return_value=bytes.fromhex('00 00 00 00'))

        # Act and assert
        with self.assertRaisesRegex(InterfaceError, 'Empty response message'):
            self.interface._read_message()

class SerialInterfaceWriteMessageTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = Mock()

        self.interface = SerialInterface(self.serial)

        self.interface.slip_serial = Mock()

    def test(self):
        # Act
        self.interface._write_message(bytes.fromhex('01 02 03 04'))

        # Assert
        self.interface.slip_serial.send_msg.assert_called_with(bytes.fromhex('00 04 01 02 03 04 00 00'))

if __name__ == '__main__':
    unittest.main()
