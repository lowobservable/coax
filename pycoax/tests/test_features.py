import unittest

import context

from coax.features import Feature, read_feature_ids, parse_features

class ReadFeatureIdsTestCase(unittest.TestCase):
    def test(self):
        commands = read_feature_ids()

        self.assertEqual(len(commands), 14)

        self.assertEqual(commands[0].feature_address, 2)
        self.assertEqual(commands[13].feature_address, 15)

class ParseFeaturesTestCase(unittest.TestCase):
    def test(self):
        commands = read_feature_ids()

        features = parse_features([None, None, None, None, None, 0x79, None, 0x99, None, None, None, None, None, None], commands)

        self.assertEqual(features, { Feature.EAB: 7 })

if __name__ == '__main__':
    unittest.main()
