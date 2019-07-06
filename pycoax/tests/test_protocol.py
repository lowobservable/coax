import unittest
from unittest.mock import Mock

import context

from coax import PollResponse, KeystrokePollResponse, ProtocolError
from coax.protocol import Command, _execute_read_command, _execute_write_command, _pack_command_word, _unpack_data_words, _unpack_data_word

class PollResponseTestCase(unittest.TestCase):
    def test_is_power_on_reset_complete(self):
        self.assertTrue(PollResponse.is_power_on_reset_complete(0b0000001010))

    def test_is_keystroke(self):
        self.assertTrue(PollResponse.is_keystroke(0b1111111110))

class KeystrokePollResponseTestCase(unittest.TestCase):
    def test(self):
        # Act
        response = KeystrokePollResponse(0b1111111110)

        # Assert
        self.assertEqual(response.scan_code, 0xff)

    def test_not_a_keystroke(self):
        with self.assertRaisesRegex(ValueError, 'Invalid keystroke poll response'):
            response = KeystrokePollResponse(0b0000001000)

class ExecuteReadCommandTestCase(unittest.TestCase):
    def setUp(self):
        self.interface = Mock()

    def test(self):
        # Arrange
        self.interface.execute = Mock(return_value=[0b0000000010])

        # Act and assert
        self.assertEqual(_execute_read_command(self.interface, Command.READ_TERMINAL_ID), bytes.fromhex('00'))

    def test_allow_trta_response(self):
        # Arrange
        self.interface.execute = Mock(return_value=[0b0000000000])

        # Act and assert
        self.assertEqual(_execute_read_command(self.interface, Command.POLL, allow_trta_response=True, trta_value='TRTA'), 'TRTA')

    def test_disable_unpack_data_words(self):
        # Arrange
        self.interface.execute = Mock(return_value=[0b1111111110])

        # Act and assert
        self.assertEqual(_execute_read_command(self.interface, Command.POLL, unpack_data_words=False), [0b1111111110])

    def test_unexpected_response_length(self):
        # Arrange
        self.interface.execute = Mock(return_value=[])

        # Act and assert
        with self.assertRaisesRegex(ProtocolError, 'Expected 1 word READ_TERMINAL_ID response'):
            _execute_read_command(self.interface, Command.READ_TERMINAL_ID)

    def test_timeout_is_passed_to_interface(self):
        # Arrange
        self.interface.execute = Mock(return_value=[0b0000000010])

        # Act
        _execute_read_command(self.interface, Command.READ_TERMINAL_ID, timeout=10)

        # Assert
        self.assertEqual(self.interface.execute.call_args[1].get('timeout'), 10)

class ExecuteWriteCommandTestCase(unittest.TestCase):
    def setUp(self):
        self.interface = Mock()

    def test(self):
        # Arrange
        self.interface.execute = Mock(return_value=[0b0000000000])

        # Act and assert
        _execute_write_command(self.interface, Command.WRITE_DATA, bytes.fromhex('de ad be ef'))

    def test_unexpected_response_length(self):
        # Arrange
        self.interface.execute = Mock(return_value=[])

        # Act and assert
        with self.assertRaisesRegex(ProtocolError, 'Expected 1 word WRITE_DATA response'):
            _execute_write_command(self.interface, Command.WRITE_DATA, bytes.fromhex('de ad be ef'))

    def test_not_trta_response(self):
        # Arrange
        self.interface.execute = Mock(return_value=[0b0000000010])

        # Act and assert
        with self.assertRaisesRegex(ProtocolError, 'Expected TR/TA response'):
            _execute_write_command(self.interface, Command.WRITE_DATA, bytes.fromhex('de ad be ef'))

    def test_timeout_is_passed_to_interface(self):
        # Arrange
        self.interface.execute = Mock(return_value=[0b0000000000])

        # Assert
        _execute_write_command(self.interface, Command.WRITE_DATA, bytes.fromhex('de ad be ef'), timeout=10)

        # Assert
        self.assertEqual(self.interface.execute.call_args[1].get('timeout'), 10)

class PackCommandWordTestCase(unittest.TestCase):
    def test_without_address(self):
        self.assertEqual(_pack_command_word(Command.POLL_ACK), 0b001000101)

    def test_with_address(self):
        self.assertEqual(_pack_command_word(Command.POLL_ACK, address=3), 0b111000101)

class UnpackDataWordsTestCase(unittest.TestCase):
    def test(self):
        self.assertEqual(_unpack_data_words([0b0000000010, 0b1111111110]), bytes.fromhex('00 ff'))

class UnpackDataWordTestCase(unittest.TestCase):
    def test(self):
        self.assertEqual(_unpack_data_word(0b0000000010), 0x00)
        self.assertEqual(_unpack_data_word(0b1111111110), 0xff)

    def test_data_bit_not_set_error(self):
        with self.assertRaisesRegex(ProtocolError, 'Word does not have data bit set'):
            _unpack_data_word(0b0000000011)
    
    def test_parity_error(self):
        with self.assertRaisesRegex(ProtocolError, 'Parity error'):
            _unpack_data_word(0b0000000000)

if __name__ == '__main__':
    unittest.main()
