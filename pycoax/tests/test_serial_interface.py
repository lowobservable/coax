import unittest
from unittest.mock import Mock, create_autospec, call
from serial import Serial
import sliplib

import context

from coax.interface import FrameFormat
from coax.serial_interface import SerialInterface
from coax.exceptions import InterfaceError, ReceiveTimeout

class SerialInterfaceResetTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = create_autospec(Serial, instance=True)

        self.serial.timeout = None

        self.interface = SerialInterface(self.serial)

        self.interface._write_message = Mock(wraps=self.interface._write_message)
        self.interface._read_message = Mock(return_value=bytes.fromhex('01 32 70'))

    def test_message_is_sent(self):
        # Act
        self.interface.reset()

        # Assert
        self.interface._write_message.assert_called_with(bytes.fromhex('01'))

    def test_non_legacy_response_is_handled_correctly(self):
        # Act
        self.interface.reset()

        # Assert
        self.assertFalse(self.interface.legacy_firmware_detected)
        self.assertIsNone(self.interface.legacy_firmware_version)

    def test_legacy_response_is_handled_correctly(self):
        # Arrange
        self.interface._read_message.return_value=bytes.fromhex('01 01 02 03')

        # Act
        self.interface.reset()

        # Assert
        self.assertTrue(self.interface.legacy_firmware_detected)
        self.assertEqual(self.interface.legacy_firmware_version, '1.2.3')

    def test_timeout_is_restored_after_reset(self):
        # Arrange
        self.serial.timeout = 123

        # Act
        self.interface.reset()

        # Assert
        self.assertEqual(self.serial.timeout, 123)

    def test_invalid_message_length_is_handled_correctly(self):
        # Arrange
        self.interface._read_message.return_value=bytes.fromhex('01 01')

        # Act and assert
        with self.assertRaisesRegex(InterfaceError, 'Invalid reset response'):
            self.interface.reset()

    def test_error_is_handled_correctly(self):
        # Arrange
        self.interface._read_message.return_value=bytes.fromhex('02 01')

        # Act and assert
        with self.assertRaisesRegex(InterfaceError, 'Invalid request message'):
            self.interface.reset()

    def test_error_with_description_is_handled_correctly(self):
        # Arrange
        self.interface._read_message.return_value=bytes.fromhex('02 01 45 72 72 6f 72 20 64 65 73 63 72 69 70 74 69 6f 6e')

        # Act and assert
        with self.assertRaisesRegex(InterfaceError, 'Invalid request message: Error description'):
            self.interface.reset()

class SerialInterfaceTransmitReceiveTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = create_autospec(Serial, instance=True)

        self.serial.timeout = None

        self.interface = SerialInterface(self.serial)

        self.interface._write_message = Mock(wraps=self.interface._write_message)
        self.interface._read_message = Mock()

    def test_words_frame(self):
        # Arrange
        self.interface._read_message.return_value=bytes.fromhex('01 00 00')

        # Act
        responses = self.interface._transmit_receive([(None, (FrameFormat.WORDS, [0b1111111111, 0b0000000000]))], [1], None)

        # Assert
        self.assertEqual(responses, [[0]])

        self.interface._write_message.assert_called_with(bytes.fromhex('06 00 00 ff 03 00 00 00 01 00 00'))

    def test_words_repeat_frame(self):
        # Arrange
        self.interface._read_message.return_value=bytes.fromhex('01 00 00')

        # Act
        responses = self.interface._transmit_receive([(None, (FrameFormat.WORDS, ([0b1111111111, 0b0000000000], 2)))], [1], None)

        # Assert
        self.assertEqual(responses, [[0]])

        self.interface._write_message.assert_called_with(bytes.fromhex('06 00 02 ff 03 00 00 00 01 00 00'))

    def test_word_data_frame(self):
        # Arrange
        self.interface._read_message.return_value=bytes.fromhex('01 00 00')

        # Act
        responses = self.interface._transmit_receive([(None, (FrameFormat.WORD_DATA, 0b1111111111, [0x00, 0xff]))], [1], None)

        # Assert
        self.assertEqual(responses, [[0]])

        self.interface._write_message.assert_called_with(bytes.fromhex('06 00 00 ff 03 02 00 fe 03 00 01 00 00'))

    def test_word_data_repeat_frame(self):
        # Arrange
        self.interface._read_message.return_value=bytes.fromhex('01 00 00')

        # Act
        responses = self.interface._transmit_receive([(None, (FrameFormat.WORD_DATA, 0b1111111111, ([0x00, 0xff], 2)))], [1], None)

        # Assert
        self.assertEqual(responses, [[0]])

        self.interface._write_message.assert_called_with(bytes.fromhex('06 80 02 ff 03 02 00 fe 03 00 01 00 00'))

    def test_data_frame(self):
        # Arrange
        self.interface._read_message.return_value=bytes.fromhex('01 00 00')

        # Act
        responses = self.interface._transmit_receive([(None, (FrameFormat.DATA, [0x00, 0xff]))], [1], None)

        # Assert
        self.assertEqual(responses, [[0]])

        self.interface._write_message.assert_called_with(bytes.fromhex('06 00 00 02 00 fe 03 00 01 00 00'))

    def test_data_repeat_frame(self):
        # Arrange
        self.interface._read_message.return_value=bytes.fromhex('01 00 00')

        # Act
        responses = self.interface._transmit_receive([(None, (FrameFormat.DATA, ([0x00, 0xff], 2)))], [1], None)

        # Assert
        self.assertEqual(responses, [[0]])

        self.interface._write_message.assert_called_with(bytes.fromhex('06 00 02 02 00 fe 03 00 01 00 00'))

    def test_receive_timeout_error(self):
        # Arrange
        self.interface._read_message.return_value=bytes.fromhex('02 66')

        # Act
        responses = self.interface._transmit_receive([(None, (FrameFormat.WORD_DATA, 0b1111111111, [0x00, 0xff]))], [1], 0.5)

        # Assert
        self.assertIsInstance(responses[0], ReceiveTimeout)

    def test_interface_error(self):
        # Arrange
        self.interface._read_message.return_value=bytes.fromhex('02 65')

        # Act and assert
        with self.assertRaises(InterfaceError):
            self.interface._transmit_receive([(None, (FrameFormat.WORD_DATA, 0b1111111111, [0x00, 0xff]))], [1], 0.5)

    def test_timeout(self):
        # Arrange
        self.interface._read_message.return_value=bytes.fromhex('01 00 00')

        # Act
        self.interface._transmit_receive([(None, (FrameFormat.WORD_DATA, 0b1111111111, [0x00, 0xff]))], [1], 0.5)

        # Assert
        self.interface._write_message.assert_called_with(bytes.fromhex('06 00 00 ff 03 02 00 fe 03 00 01 01 f4'))

    def test_addressed_frame(self):
        with self.assertRaises(NotImplementedError):
            self.interface._transmit_receive([(0b111000, (FrameFormat.WORD_DATA, 0b1111111111, [0x00, 0xff]))], [1], 0.5)

    def test_multiple_frames(self):
        # Arrange
        self.interface._read_message.return_value=bytes.fromhex('01 00 00')

        # Act
        responses = self.interface._transmit_receive([(None, (FrameFormat.WORDS, [0b1111111111, 0b0000000000])), (None, (FrameFormat.WORD_DATA, 0b1111111111, [0x00, 0xff]))], [1, 1], None)

        # Assert
        self.assertEqual(responses, [[0], [0]])

        self.interface._write_message.assert_has_calls([call(bytes.fromhex('06 00 00 ff 03 00 00 00 01 00 00')), call(bytes.fromhex('06 00 00 ff 03 02 00 fe 03 00 01 00 00'))])

class SerialInterfaceReadMessageTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = create_autospec(Serial, instance=True)

        self.interface = SerialInterface(self.serial)

        self.interface.slip_serial = Mock(wraps=self.interface.slip_serial)

    def test(self):
        # Arrange
        self.interface.slip_serial.recv_msg.return_value=bytes.fromhex('00 04 01 02 03 04 00 00')

        # Act
        message = self.interface._read_message()

        # Assert
        self.assertEqual(message, bytes.fromhex('01 02 03 04'))

    def test_protocol_error_is_handled_correctly(self):
        # Arrange
        self.interface.slip_serial.recv_msg.side_effect=sliplib.ProtocolError

        # Act and assert
        with self.assertRaisesRegex(InterfaceError, 'SLIP protocol error'):
            self.interface._read_message()

    def test_invalid_message_length_is_handled_correctly(self):
        # Arrange
        self.interface.slip_serial.recv_msg.return_value=bytes.fromhex('00')

        # Act and assert
        with self.assertRaisesRegex(InterfaceError, 'Invalid response message'):
            self.interface._read_message()

    def test_message_length_mismatch_is_handled_correctly(self):
        # Arrange
        self.interface.slip_serial.recv_msg.return_value=bytes.fromhex('00 05 01 02 03 04 00 00')

        # Act and assert
        with self.assertRaisesRegex(InterfaceError, 'Response message length mismatch'):
            self.interface._read_message()

    def test_empty_message_is_handled_correctly(self):
        # Arrange
        self.interface.slip_serial.recv_msg.return_value=bytes.fromhex('00 00 00 00')

        # Act and assert
        with self.assertRaisesRegex(InterfaceError, 'Empty response message'):
            self.interface._read_message()

class SerialInterfaceWriteMessageTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = create_autospec(Serial, instance=True)

        self.interface = SerialInterface(self.serial)

        self.interface.slip_serial = Mock(wraps=self.interface.slip_serial)

    def test(self):
        # Act
        self.interface._write_message(bytes.fromhex('01 02 03 04'))

        # Assert
        self.interface.slip_serial.send_msg.assert_called_with(bytes.fromhex('00 04 01 02 03 04 00 00'))

if __name__ == '__main__':
    unittest.main()
