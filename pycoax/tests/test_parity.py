import unittest

import context

from coax.parity import even_parity, odd_parity

class EvenParityTestCase(unittest.TestCase):
    def test_with_even_input(self):
        self.assertEqual(even_parity(0b00000000), 0)

    def test_with_odd_input(self):
        self.assertEqual(even_parity(0b00000001), 1)

    def test_with_out_of_range_input(self):
        for input in [-1, 256]:
            with self.subTest(input=input):
                with self.assertRaises(ValueError):
                    even_parity(input)

class OddParityTestCase(unittest.TestCase):
    def test_with_even_input(self):
        self.assertEqual(odd_parity(0b00000000), 1)

    def test_with_odd_input(self):
        self.assertEqual(odd_parity(0b00000001), 0)

    def test_with_out_of_range_input(self):
        for input in [-1, 256]:
            with self.subTest(input=input):
                with self.assertRaises(ValueError):
                    odd_parity(input)

if __name__ == '__main__':
    unittest.main()
