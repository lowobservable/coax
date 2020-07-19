import unittest
from unittest.mock import Mock, call, patch

import context

from coax.features import Feature, get_features

class GetFeaturesTestCase(unittest.TestCase):
    def setUp(self):
        self.interface = Mock()

        patcher = patch('coax.features.read_feature_id')

        self.read_feature_id_mock = patcher.start()

        self.addCleanup(patch.stopall)

    def test_with_known_feature(self):
        # Arrange
        def read_feature_id(interface, feature_address, **kwargs):
            if feature_address == 7:
                return 0x79

            return None

        self.read_feature_id_mock.side_effect = read_feature_id

        # Act
        features = get_features(self.interface)

        # Assert
        self.assertEqual(features, { Feature.EAB: 7 })

    def test_with_unknown_feature(self):
        # Arrange
        def read_feature_id(interface, feature_address, **kwargs):
            if feature_address == 7:
                return 0x99

            return None

        self.read_feature_id_mock.side_effect = read_feature_id

        # Act
        features = get_features(self.interface)

        # Assert
        self.assertEqual(features, { })

    def test_all_feature_addresses_are_enumerated(self):
        # Act
        features = get_features(self.interface)

        # Assert
        calls = self.read_feature_id_mock.call_args_list

        self.assertEqual(calls, [call(self.interface, address) for address in range(2, 16)])

    def test_receive_timeout_is_passed_to_read_feature_id(self):
        # Act
        features = get_features(self.interface, receive_timeout=10)

        # Assert
        calls = self.read_feature_id_mock.call_args_list

        self.assertEqual(calls, [call(self.interface, address, receive_timeout=10) for address in range(2, 16)])

if __name__ == '__main__':
    unittest.main()
