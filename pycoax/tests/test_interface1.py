import unittest
from unittest.mock import Mock
import sliplib

import context

from coax import Interface1, InterfaceError, ReceiveError, ReceiveTimeout

class Interface1ResetTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = Mock()

        self.serial.timeout = None

        self.interface = Interface1(self.serial)

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

class Interface1ExecuteTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = Mock()

        self.serial.timeout = None

        self.interface = Interface1(self.serial)

        self.interface._write_message = Mock()
        self.interface._read_message = Mock(return_value=bytes.fromhex('01 00'))

    def test_message_is_sent_without_data(self):
        # Act
        self.interface.execute(0b0000001001)

        # Assert
        self.interface._write_message.assert_called_with(bytes.fromhex('02 00 09 00 01 00 00'))

    def test_message_is_sent_with_data(self):
        # Act
        self.interface.execute(0b0000110001, data=bytes.fromhex('de ad be ef'))

        # Assert
        self.interface._write_message.assert_called_with(bytes.fromhex('02 00 31 00 01 00 00 de ad be ef'))

    def test_message_is_sent_with_response_length(self):
        # Act
        self.interface.execute(0b0000011101, response_length=4)

        # Assert
        self.interface._write_message.assert_called_with(bytes.fromhex('02 00 1d 00 04 00 00'))

    def test_timeout_cannot_exceed_serial_timeout(self):
        # Arrange
        self.serial.timeout = 2.0

        # Act and assert
        with self.assertRaisesRegex(ValueError, 'Timeout cannot be greater than serial timeout'):
            self.interface.execute(0b0000000101, timeout=3)

    def test_message_is_sent_with_timeout(self):
        # Act
        self.interface.execute(0b0000000101, timeout=3)

        # Assert
        self.interface._write_message.assert_called_with(bytes.fromhex('02 00 05 00 01 0b b8'))

    # TODO... interface timeout...

    def test_receive_timeout_is_handled_correctly(self):
        # Arrange
        self.interface._read_message = Mock(return_value=bytes.fromhex('02 66'))

        # Act and assert
        with self.assertRaises(ReceiveTimeout):
            self.interface.execute(0b0000000101)

    def test_receive_error_is_handled_correctly(self):
        # Arrange
        self.interface._read_message = Mock(return_value=bytes.fromhex('02 67'))

        # Act and assert
        with self.assertRaisesRegex(ReceiveError, 'Receiver buffer overflow'):
            self.interface.execute(0b0000000101)

    def test_interface_error_is_handled_correctly(self):
        # Arrange
        self.interface._read_message = Mock(return_value=bytes.fromhex('03'))

        # Act and assert
        with self.assertRaisesRegex(InterfaceError, 'Invalid response'):
            self.interface.execute(0b0000000101)

    def test_response_words_are_unpacked(self):
        # Arrange
        self.interface._read_message = Mock(return_value=bytes.fromhex('01 01 02 03 04'))

        # Act
        response_words = self.interface.execute(0b0000011101, response_length=4)

        # Assert
        self.assertEqual(response_words, [0x0201, 0x0403])

    def test_receiver_error_is_handled_correctly(self):
        # Arrange
        self.interface._read_message = Mock(return_value=bytes.fromhex('01 a0 80'))

        # Act and assert
        with self.assertRaisesRegex(ReceiveError, 'Receiver STARTING_SEQUENCE error'):
            self.interface.execute(0b0000011101, response_length=4)

class Interface1OffloadLoadAddressCounterTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = Mock()

        self.interface = Interface1(self.serial)

        self.interface._execute_offload = Mock()

    def test(self):
        # Act
        self.interface.offload_load_address_counter(960)

        # Assert
        self.interface._execute_offload.assert_called_with(0x01, bytes.fromhex('03 c0'))

class Interface1OffloadWriteTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = Mock()

        self.interface = Interface1(self.serial)

        self.interface._execute_offload = Mock()

    def test_message_is_sent_with_data(self):
        # Act
        self.interface.offload_write(bytes.fromhex('de ad be ef'))

        # Assert
        self.interface._execute_offload.assert_called_with(0x02, bytes.fromhex('ff ff 00 00 00 de ad be ef'))

    def test_message_is_sent_with_address(self):
        # Act
        self.interface.offload_write(bytes.fromhex('de ad be ef'), address=960)

        # Assert
        self.interface._execute_offload.assert_called_with(0x02, bytes.fromhex('03 c0 00 00 00 de ad be ef'))

    def test_message_is_sent_with_restore_original_address(self):
        # Act
        self.interface.offload_write(bytes.fromhex('de ad be ef'), restore_original_address=True)

        # Assert
        self.interface._execute_offload.assert_called_with(0x02, bytes.fromhex('ff ff 01 00 00 de ad be ef'))

    def test_message_is_sent_with_repeat(self):
        # Act
        self.interface.offload_write(bytes.fromhex('de ad be ef'), repeat=1)

        # Assert
        self.interface._execute_offload.assert_called_with(0x02, bytes.fromhex('ff ff 00 00 01 de ad be ef'))

class Interface1ReadMessageTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = Mock()

        self.interface = Interface1(self.serial)

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

class Interface1WriteMessageTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = Mock()

        self.interface = Interface1(self.serial)

        self.interface.slip_serial = Mock()

    def test(self):
        # Act
        self.interface._write_message(bytes.fromhex('01 02 03 04'))

        # Assert
        self.interface.slip_serial.send_msg.assert_called_with(bytes.fromhex('00 04 01 02 03 04 00 00'))

if __name__ == '__main__':
    unittest.main()
