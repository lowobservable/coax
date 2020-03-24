import unittest
from unittest.mock import Mock

import context

from coax import PollResponse, KeystrokePollResponse, ProtocolError
from coax.protocol import Command, Status, TerminalId, Control, SecondaryControl, pack_command_word, unpack_command_word, pack_data_word, unpack_data_word, pack_data_words, unpack_data_words, _execute_read_command, _execute_write_command

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

class StatusTestCase(unittest.TestCase):
    def test(self):
        status = Status(0b10000110)

        self.assertTrue(status.monocase)
        self.assertTrue(status.busy)
        self.assertTrue(status.feature_error)
        self.assertTrue(status.operation_complete)

class TerminalIdTestCase(unittest.TestCase):
    def test_model_2(self):
        terminal_id = TerminalId(0b00000100)

        self.assertEqual(terminal_id.model, 2)

    def test_model_3(self):
        terminal_id = TerminalId(0b00000110)

        self.assertEqual(terminal_id.model, 3)

    def test_model_4(self):
        terminal_id = TerminalId(0b00001110)

        self.assertEqual(terminal_id.model, 4)

    def test_model_5(self):
        terminal_id = TerminalId(0b00001100)

        self.assertEqual(terminal_id.model, 5)

    def test_invalid_identifier(self):
        with self.assertRaisesRegex(ValueError, 'Invalid terminal identifier'):
            terminal_id = TerminalId(0b00000001)

    def test_invalid_model(self):
        with self.assertRaisesRegex(ValueError, 'Invalid model'):
            terminal_id = TerminalId(0b00000000)

class ControlTestCase(unittest.TestCase):
    def test_step_inhibit(self):
        control = Control(step_inhibit=True)

        self.assertEqual(control.value, 0b00010000)

    def test_display_inhibit(self):
        control = Control(display_inhibit=True)

        self.assertEqual(control.value, 0b00001000)

    def test_cursor_inhibit(self):
        control = Control(cursor_inhibit=True)

        self.assertEqual(control.value, 0b00000100)

    def test_cursor_reverse(self):
        control = Control(cursor_reverse=True)

        self.assertEqual(control.value, 0b00000010)

    def test_cursor_blink(self):
        control = Control(cursor_blink=True)

        self.assertEqual(control.value, 0b00000001)

class SecondaryControlTestCase(unittest.TestCase):
    def test_big(self):
        control = SecondaryControl(big=True)

        self.assertEqual(control.value, 0b00000001)

class PackCommandWordTestCase(unittest.TestCase):
    def test(self):
        self.assertEqual(pack_command_word(Command.POLL_ACK), 0b0001000101)

class UnpackCommandWordTestCase(unittest.TestCase):
    def test(self):
        # Act
        command = unpack_command_word(0b0001000101)

        # Assert
        self.assertEqual(command, Command.POLL_ACK)

    def test_command_bit_not_set_error(self):
        with self.assertRaisesRegex(ProtocolError, 'Word does not have command bit set'):
            unpack_command_word(0b0001000100)

class PackDataWordTestCase(unittest.TestCase):
    def test(self):
        self.assertEqual(pack_data_word(0x00), 0b0000000010)
        self.assertEqual(pack_data_word(0x01), 0b0000000100)
        self.assertEqual(pack_data_word(0xff), 0b1111111110)

    def test_disable_set_parity(self):
        self.assertEqual(pack_data_word(0x00, set_parity=False), 0b0000000000)
        self.assertEqual(pack_data_word(0x01, set_parity=False), 0b0000000100)
        self.assertEqual(pack_data_word(0xff, set_parity=False), 0b1111111100)

class UnpackDataWordTestCase(unittest.TestCase):
    def test(self):
        self.assertEqual(unpack_data_word(0b0000000010), 0x00)
        self.assertEqual(unpack_data_word(0b1111111110), 0xff)

    def test_data_bit_not_set_error(self):
        with self.assertRaisesRegex(ProtocolError, 'Word does not have data bit set'):
            unpack_data_word(0b0000000011)
    
    def test_parity_error(self):
        with self.assertRaisesRegex(ProtocolError, 'Parity error'):
            unpack_data_word(0b0000000000, check_parity=True)

class PackDataWordsTestCase(unittest.TestCase):
    def test(self):
        self.assertEqual(pack_data_words(bytes.fromhex('00 ff')), [0b0000000010, 0b1111111110])

class UnpackDataWordsTestCase(unittest.TestCase):
    def test(self):
        self.assertEqual(unpack_data_words([0b0000000010, 0b1111111110]), bytes.fromhex('00 ff'))

class ExecuteReadCommandTestCase(unittest.TestCase):
    def setUp(self):
        self.interface = Mock()

    def test(self):
        # Arrange
        command_word = pack_command_word(Command.READ_TERMINAL_ID)

        self.interface.transmit_receive = Mock(return_value=[0b0000000010])

        # Act and assert
        self.assertEqual(_execute_read_command(self.interface, command_word), bytes.fromhex('00'))

    def test_allow_trta_response(self):
        # Arrange
        command_word = pack_command_word(Command.POLL)

        self.interface.transmit_receive = Mock(return_value=[0b0000000000])

        # Act and assert
        self.assertEqual(_execute_read_command(self.interface, command_word, allow_trta_response=True, trta_value='TRTA'), 'TRTA')

    def test_disable_unpack(self):
        # Arrange
        command_word = pack_command_word(Command.POLL)

        self.interface.transmit_receive = Mock(return_value=[0b1111111110])

        # Act and assert
        self.assertEqual(_execute_read_command(self.interface, command_word, unpack=False), [0b1111111110])

    def test_unexpected_response_length(self):
        # Arrange
        command_word = pack_command_word(Command.READ_TERMINAL_ID)

        self.interface.transmit_receive = Mock(return_value=[])

        # Act and assert
        with self.assertRaisesRegex(ProtocolError, 'Expected 1 word READ_TERMINAL_ID response'):
            _execute_read_command(self.interface, command_word)

    def test_receive_timeout_is_passed_to_interface(self):
        # Arrange
        command_word = pack_command_word(Command.READ_TERMINAL_ID)

        self.interface.transmit_receive = Mock(return_value=[0b0000000010])

        # Act
        _execute_read_command(self.interface, command_word, receive_timeout=10)

        # Assert
        self.assertEqual(self.interface.transmit_receive.call_args[1].get('receive_timeout'), 10)

class ExecuteWriteCommandTestCase(unittest.TestCase):
    def setUp(self):
        self.interface = Mock()

    def test(self):
        # Arrange
        command_word = pack_command_word(Command.WRITE_DATA)

        self.interface.transmit_receive = Mock(return_value=[0b0000000000])

        # Act and assert
        _execute_write_command(self.interface, command_word, bytes.fromhex('de ad be ef'))

    def test_unexpected_response_length(self):
        # Arrange
        command_word = pack_command_word(Command.WRITE_DATA)

        self.interface.transmit_receive = Mock(return_value=[])

        # Act and assert
        with self.assertRaisesRegex(ProtocolError, 'Expected 1 word WRITE_DATA response'):
            _execute_write_command(self.interface, command_word, bytes.fromhex('de ad be ef'))

    def test_not_trta_response(self):
        # Arrange
        command_word = pack_command_word(Command.WRITE_DATA)

        self.interface.transmit_receive = Mock(return_value=[0b0000000010])

        # Act and assert
        with self.assertRaisesRegex(ProtocolError, 'Expected TR/TA response'):
            _execute_write_command(self.interface, command_word, bytes.fromhex('de ad be ef'))

    def test_receive_timeout_is_passed_to_interface(self):
        # Arrange
        command_word = pack_command_word(Command.WRITE_DATA)

        self.interface.transmit_receive = Mock(return_value=[0b0000000000])

        # Assert
        _execute_write_command(self.interface, command_word, bytes.fromhex('de ad be ef'), receive_timeout=10)

        # Assert
        self.assertEqual(self.interface.transmit_receive.call_args[1].get('receive_timeout'), 10)

if __name__ == '__main__':
    unittest.main()
