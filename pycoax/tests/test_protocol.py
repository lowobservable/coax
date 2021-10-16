import unittest

import context

from coax.interface import FrameFormat
from coax.protocol import PollAction, PowerOnResetCompletePollResponse, KeystrokePollResponse, TerminalId, TerminalType, Control, SecondaryControl, Poll, PollAck, ReadStatus, ReadTerminalId, ReadExtendedId, ReadAddressCounterHi, ReadAddressCounterLo, ReadData, ReadMultiple, Reset, LoadControlRegister, LoadSecondaryControl, LoadMask, LoadAddressCounterHi, LoadAddressCounterLo, WriteData, Clear, SearchForward, SearchBackward, InsertByte, StartOperation, DiagnosticReset, ReadFeatureId, pack_data_word, unpack_data_word, pack_data_words, unpack_data_words
from coax.exceptions import ProtocolError

class TerminalIdTestCase(unittest.TestCase):
    def test_cut_model_2(self):
        terminal_id = TerminalId(0b00000100)

        self.assertEqual(terminal_id.type, TerminalType.CUT)
        self.assertEqual(terminal_id.model, 2)

    def test_cut_model_3(self):
        terminal_id = TerminalId(0b00000110)

        self.assertEqual(terminal_id.type, TerminalType.CUT)
        self.assertEqual(terminal_id.model, 3)

    def test_cut_model_4(self):
        terminal_id = TerminalId(0b00001110)

        self.assertEqual(terminal_id.type, TerminalType.CUT)
        self.assertEqual(terminal_id.model, 4)

    def test_cut_model_5(self):
        terminal_id = TerminalId(0b00001100)

        self.assertEqual(terminal_id.type, TerminalType.CUT)
        self.assertEqual(terminal_id.model, 5)

    def test_dft(self):
        terminal_id = TerminalId(0b00000001)

        self.assertEqual(terminal_id.type, TerminalType.DFT)

    def test_invalid_identifier(self):
        with self.assertRaisesRegex(ValueError, 'Invalid terminal identifier'):
            terminal_id = TerminalId(0b00000011)

    def test_invalid_cut_model(self):
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

class PollTestCase(unittest.TestCase):
    def test_pack_poll_action_none(self):
        self.assertEqual(Poll(PollAction.NONE).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_00001_01))

    def test_pack_poll_action_alarm(self):
        self.assertEqual(Poll(PollAction.ALARM).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b100_00001_01))

    def test_pack_poll_action_enable_keyboard_clicker(self):
        self.assertEqual(Poll(PollAction.ENABLE_KEYBOARD_CLICKER).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b110_00001_01))

    def test_pack_poll_action_disable_keyboard_clicker(self):
        self.assertEqual(Poll(PollAction.DISABLE_KEYBOARD_CLICKER).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b010_00001_01))

    def test_unpack_tt_ar(self):
        self.assertIsNone(Poll().unpack_inbound_frame([0b0000000000]))

    def test_unpack_power_on_reset_complete(self):
        self.assertIsInstance(Poll().unpack_inbound_frame([0b00000010_10]), PowerOnResetCompletePollResponse)

    def test_unpack_keystroke(self):
        poll_response = Poll().unpack_inbound_frame([0b01010001_10])

        self.assertIsInstance(poll_response, KeystrokePollResponse)

        self.assertEqual(poll_response.scan_code, 0x51)

    def test_unpack_invalid_response(self):
        for words in [[], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    Poll().unpack_inbound_frame(words)

class PollAckTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(PollAck().pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_10001_01))

    def test_unpack_tt_ar(self):
        self.assertIsNone(PollAck().unpack_inbound_frame([0b0000000000]))

    def test_unpack_invalid_response(self):
        for words in [[], [0b1010101011], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    PollAck().unpack_inbound_frame(words)

class ReadStatusTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(ReadStatus().pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_01101_01))

    def test_unpack_all_false(self):
        status = ReadStatus().unpack_inbound_frame([0b00100000_00])

        self.assertFalse(status.monocase)
        self.assertFalse(status.busy)
        self.assertFalse(status.feature_error)
        self.assertFalse(status.operation_complete)

    def test_unpack_all_true(self):
        status = ReadStatus().unpack_inbound_frame([0b10000110_00])

        self.assertTrue(status.monocase)
        self.assertTrue(status.busy)
        self.assertTrue(status.feature_error)
        self.assertTrue(status.operation_complete)

    def test_unpack_invalid_response(self):
        for words in [[], [0b1010101011], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    ReadStatus().unpack_inbound_frame(words)

class ReadTerminalIdTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(ReadTerminalId().pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_01001_01))

    def test_unpack_cut_terminal(self):
        terminal_id = ReadTerminalId().unpack_inbound_frame([0b1111_010_0_00])

        self.assertEqual(terminal_id.type, TerminalType.CUT)
        self.assertEqual(terminal_id.model, 2);
        self.assertEqual(terminal_id.keyboard, 15)

    def test_unpack_dft_terminal(self):
        terminal_id = ReadTerminalId().unpack_inbound_frame([0b0000_000_1_00])

        self.assertEqual(terminal_id.type, TerminalType.DFT)
        self.assertIsNone(terminal_id.model)
        self.assertIsNone(terminal_id.keyboard)

    def test_unpack_invalid_response(self):
        for words in [[], [0b1010101011], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    ReadTerminalId().unpack_inbound_frame(words)

class ReadExtendedIdTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(ReadExtendedId().pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_00111_01))

    def test_unpack_extended_id(self):
        self.assertEqual(ReadExtendedId().unpack_inbound_frame([0b11000001_00, 0b00110100_00, 0b10000011_00, 0b00000000_00]), bytes.fromhex('c1 34 83 00'))

    def test_unpack_invalid_response(self):
        for words in [[], [0b11000001_00, 0b00110100_00, 0b10000011_01, 0b00000000_00], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    ReadExtendedId().unpack_inbound_frame(words)

class ReadAddressCounterHiTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(ReadAddressCounterHi().pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_00101_01))

    def test_unpack_address(self):
        self.assertEqual(ReadAddressCounterHi().unpack_inbound_frame([0b00000010_00]), 0x02)

    def test_unpack_invalid_response(self):
        for words in [[], [0b00000010_01], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    ReadAddressCounterHi().unpack_inbound_frame(words)

class ReadAddressCounterLoTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(ReadAddressCounterLo().pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_10101_01))

    def test_unpack_address(self):
        self.assertEqual(ReadAddressCounterLo().unpack_inbound_frame([0b11111111_00]), 0xff)

    def test_unpack_invalid_response(self):
        for words in [[], [0b11111111_01], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    ReadAddressCounterLo().unpack_inbound_frame(words)

class ReadDataTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(ReadData().pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_00011_01))

    def test_unpack_data(self):
        self.assertEqual(ReadData().unpack_inbound_frame([0b11111111_00]), 0xff)

    def test_unpack_invalid_response(self):
        for words in [[], [0b11111111_01], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    ReadData().unpack_inbound_frame(words)

class ReadMultipleTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(ReadMultiple().pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_01011_01))

    def test_unpack_data(self):
        self.assertEqual(ReadMultiple().unpack_inbound_frame([0b00000000_00, 0b11111111_00]), bytes.fromhex('00 ff'))

    def test_unpack_invalid_response(self):
        for words in [[], [0b11111111_01]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    ReadMultiple().unpack_inbound_frame(words)

class ResetTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(Reset().pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_00010_01))

    def test_unpack_tt_ar(self):
        self.assertIsNone(Reset().unpack_inbound_frame([0b0000000000]))

    def test_unpack_invalid_response(self):
        for words in [[], [0b0011000000], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    Reset().unpack_inbound_frame(words)

class LoadControlRegisterTestCase(unittest.TestCase):
    def test_pack_all_false(self):
        control = Control(False, False, False, False, False)

        self.assertEqual(LoadControlRegister(control).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_01010_01, [0b00000000]))

    def test_pack_all_true(self):
        control = Control(True, True, True, True, True)

        self.assertEqual(LoadControlRegister(control).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_01010_01, [0b00011111]))

    def test_unpack_tt_ar(self):
        control = Control()

        self.assertIsNone(LoadControlRegister(control).unpack_inbound_frame([0b0000000000]))

    def test_unpack_invalid_response(self):
        control = Control()

        for words in [[], [0b0011000000], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    LoadControlRegister(control).unpack_inbound_frame(words)

class LoadSecondaryControlTestCase(unittest.TestCase):
    def test_pack_all_false(self):
        control = SecondaryControl(False)

        self.assertEqual(LoadSecondaryControl(control).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_11010_01, [0b00000000]))

    def test_pack_all_true(self):
        control = SecondaryControl(True)

        self.assertEqual(LoadSecondaryControl(control).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_11010_01, [0b00000001]))

    def test_unpack_tt_ar(self):
        control = SecondaryControl()

        self.assertIsNone(LoadSecondaryControl(control).unpack_inbound_frame([0b0000000000]))

    def test_unpack_invalid_response(self):
        control = SecondaryControl()

        for words in [[], [0b0011000000], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    LoadSecondaryControl(control).unpack_inbound_frame(words)

class LoadMaskTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(LoadMask(0xff).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_10110_01, [0xff]))

    def test_unpack_tt_ar(self):
        self.assertIsNone(LoadMask(0xff).unpack_inbound_frame([0b0000000000]))

    def test_unpack_invalid_response(self):
        for words in [[], [0b0011000000], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    LoadMask(0xff).unpack_inbound_frame(words)

class LoadAddressCounterHiTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(LoadAddressCounterHi(0xff).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_00100_01, [0xff]))

    def test_unpack_tt_ar(self):
        self.assertIsNone(LoadAddressCounterHi(0xff).unpack_inbound_frame([0b0000000000]))

    def test_unpack_invalid_response(self):
        for words in [[], [0b0011000000], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    LoadAddressCounterHi(0xff).unpack_inbound_frame(words)

class LoadAddressCounterLoTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(LoadAddressCounterLo(0xff).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_10100_01, [0xff]))

    def test_unpack_tt_ar(self):
        self.assertIsNone(LoadAddressCounterLo(0xff).unpack_inbound_frame([0b0000000000]))

    def test_unpack_invalid_response(self):
        for words in [[], [0b0011000000], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    LoadAddressCounterLo(0xff).unpack_inbound_frame(words)

class WriteDataTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(WriteData(bytes.fromhex('00 ff')).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_01100_01, bytes.fromhex('00 ff')))

    def test_unpack_tt_ar(self):
        self.assertIsNone(WriteData(bytes.fromhex('00 ff')).unpack_inbound_frame([0b0000000000]))

    def test_unpack_invalid_response(self):
        for words in [[], [0b0011000000], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    WriteData(bytes.fromhex('00 ff')).unpack_inbound_frame(words)

class ClearTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(Clear(0xff).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_00110_01, [0xff]))

    def test_unpack_tt_ar(self):
        self.assertIsNone(Clear(0xff).unpack_inbound_frame([0b0000000000]))

    def test_unpack_invalid_response(self):
        for words in [[], [0b0011000000], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    Clear(0xff).unpack_inbound_frame(words)

class SearchForwardTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(SearchForward(0xff).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_10000_01, [0xff]))

    def test_unpack_tt_ar(self):
        self.assertIsNone(SearchForward(0xff).unpack_inbound_frame([0b0000000000]))

    def test_unpack_invalid_response(self):
        for words in [[], [0b0011000000], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    SearchForward(0xff).unpack_inbound_frame(words)

class SearchBackwardTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(SearchBackward(0xff).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_10010_01, [0xff]))

    def test_unpack_tt_ar(self):
        self.assertIsNone(SearchBackward(0xff).unpack_inbound_frame([0b0000000000]))

    def test_unpack_invalid_response(self):
        for words in [[], [0b0011000000], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    SearchBackward(0xff).unpack_inbound_frame(words)

class InsertByteTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(InsertByte(0xff).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b000_01110_01, [0xff]))

    def test_unpack_tt_ar(self):
        self.assertIsNone(InsertByte(0xff).unpack_inbound_frame([0b0000000000]))

    def test_unpack_invalid_response(self):
        for words in [[], [0b0011000000], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    InsertByte(0xff).unpack_inbound_frame(words)

class StartOperationTestCase(unittest.TestCase):
    def test_pack(self):
        with self.assertRaises(NotImplementedError):
            StartOperation().pack_outbound_frame()

    def test_unpack(self):
        with self.assertRaises(NotImplementedError):
            StartOperation().unpack_inbound_frame([])

class DiagnosticResetTestCase(unittest.TestCase):
    def test_pack(self):
        with self.assertRaises(NotImplementedError):
            DiagnosticReset().pack_outbound_frame()

    def test_unpack(self):
        with self.assertRaises(NotImplementedError):
            DiagnosticReset().unpack_inbound_frame([])

class ReadFeatureIdTestCase(unittest.TestCase):
    def test_pack(self):
        self.assertEqual(ReadFeatureId(7).pack_outbound_frame(), (FrameFormat.WORD_DATA, 0b0111_0111_01))

    def test_unpack_tt_ar(self):
        self.assertIsNone(ReadFeatureId(7).unpack_inbound_frame([0b0000000000]))

    def test_unpack_id(self):
        self.assertEqual(ReadFeatureId(7).unpack_inbound_frame([0b01111001_00]), 0x79)

    def test_unpack_invalid_response(self):
        for words in [[], [1, 2]]:
            with self.subTest(words=words):
                with self.assertRaises(ProtocolError):
                    ReadFeatureId(7).unpack_inbound_frame(words)

class PackDataWordTestCase(unittest.TestCase):
    def test_set_parity(self):
        self.assertEqual(pack_data_word(0x00, set_parity=True), 0b00000000_10)
        self.assertEqual(pack_data_word(0x01, set_parity=True), 0b00000001_00)
        self.assertEqual(pack_data_word(0xff, set_parity=True), 0b11111111_10)

    def test_do_not_set_parity(self):
        self.assertEqual(pack_data_word(0x00, set_parity=False), 0b00000000_00)
        self.assertEqual(pack_data_word(0x01, set_parity=False), 0b00000001_00)
        self.assertEqual(pack_data_word(0xff, set_parity=False), 0b11111111_00)

class UnpackDataWordTestCase(unittest.TestCase):
    def test_do_not_check_parity(self):
        self.assertEqual(unpack_data_word(0b00000000_10, check_parity=True), 0x00)
        self.assertEqual(unpack_data_word(0b11111111_10, check_parity=True), 0xff)

    def test_data_bit_not_set_error(self):
        with self.assertRaisesRegex(ProtocolError, 'Word does not have data bit set'):
            unpack_data_word(0b00000000_11)

    def test_parity_error(self):
        with self.assertRaisesRegex(ProtocolError, 'Parity error'):
            unpack_data_word(0b00000000_00, check_parity=True)

class PackDataWordsTestCase(unittest.TestCase):
    def test(self):
        self.assertEqual(pack_data_words(bytes.fromhex('00 ff')), [0b00000000_10, 0b11111111_10])

class UnpackDataWordsTestCase(unittest.TestCase):
    def test(self):
        self.assertEqual(unpack_data_words([0b00000000_10, 0b11111111_10]), bytes.fromhex('00 ff'))

if __name__ == '__main__':
    unittest.main()
