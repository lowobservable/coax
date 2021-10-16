import unittest
from unittest.mock import Mock

import context

from coax.interface import Interface, FrameFormat
from coax.protocol import ReadAddressCounterHi, ReadAddressCounterLo
from coax.exceptions import ReceiveTimeout

class InterfaceExecuteTestCase(unittest.TestCase):
    def setUp(self):
        self.interface = Interface()

        self.interface._transmit_receive = Mock()

    def test_single_command(self):
        # Arrange
        self.interface._transmit_receive.return_value=[[0b00000010_00]]

        # Act
        response = self.interface.execute(ReadAddressCounterHi())

        # Assert
        self.assertEqual(response, 0x02)

        self.interface._transmit_receive.assert_called_once()

        (outbound_frames, response_lengths, _) = self.interface._transmit_receive.call_args[0]

        self.assertEqual(outbound_frames, [(None, (FrameFormat.WORD_DATA, 0b000_00101_01))])
        self.assertEqual(response_lengths, [1])

    def test_single_addressed_command(self):
        # Arrange
        self.interface._transmit_receive.return_value=[[0b00000010_00]]

        # Act
        response = self.interface.execute((0b111000, ReadAddressCounterHi()))

        # Assert
        self.assertEqual(response, 0x02)

        self.interface._transmit_receive.assert_called_once()

        (outbound_frames, response_lengths, _) = self.interface._transmit_receive.call_args[0]

        self.assertEqual(outbound_frames, [(0b111000, (FrameFormat.WORD_DATA, 0b000_00101_01))])
        self.assertEqual(response_lengths, [1])

    def test_multiple_commands(self):
        # Arrange
        self.interface._transmit_receive.return_value=[[0b00000010_00], [0b11111111_00]]

        # Act
        response = self.interface.execute([ReadAddressCounterHi(), ReadAddressCounterLo()])

        # Assert
        self.assertEqual(response, [0x02, 0xff])

        self.interface._transmit_receive.assert_called_once()

        (outbound_frames, response_lengths, _) = self.interface._transmit_receive.call_args[0]

        self.assertEqual(outbound_frames, [(None, (FrameFormat.WORD_DATA, 0b000_00101_01)), (None, (FrameFormat.WORD_DATA, 0b000_10101_01))])
        self.assertEqual(response_lengths, [1, 1])

    def test_multiple_addressed_commands(self):
        # Arrange
        self.interface._transmit_receive.return_value=[[0b00000010_00], [0b11111111_00]]

        # Act
        response = self.interface.execute([(0b111000, ReadAddressCounterHi()), (0b111000, ReadAddressCounterLo())])

        # Assert
        self.assertEqual(response, [0x02, 0xff])

        self.interface._transmit_receive.assert_called_once()

        (outbound_frames, response_lengths, _) = self.interface._transmit_receive.call_args[0]

        self.assertEqual(outbound_frames, [(0b111000, (FrameFormat.WORD_DATA, 0b000_00101_01)), (0b111000, (FrameFormat.WORD_DATA, 0b000_10101_01))])
        self.assertEqual(response_lengths, [1, 1])

    def test_timeout(self):
        # Arrange
        self.interface._transmit_receive.return_value=[[0b00000010_00]]

        # Act
        response = self.interface.execute(ReadAddressCounterHi(), timeout=0.1)

        # Assert
        self.interface._transmit_receive.assert_called_once()

        (_, _, timeout) = self.interface._transmit_receive.call_args[0]

        self.assertEqual(timeout, 0.1)

    def test_single_command_exception(self):
        # Arrange
        self.interface._transmit_receive.return_value=[ReceiveTimeout()]

        # Act and assert
        with self.assertRaises(ReceiveTimeout):
            self.interface.execute(ReadAddressCounterHi())

if __name__ == '__main__':
    unittest.main()
