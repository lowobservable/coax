"""
coax.features
~~~~~~~~~~~~~
"""

from enum import Enum

from .protocol import ReadFeatureId

class Feature(Enum):
    """Terminal feature."""

    EAB = 0x79

FEATURE_ADDRESS_MIN = 2
FEATURE_ADDRESS_MAX = 15

FEATURE_ADDRESSES = range(FEATURE_ADDRESS_MIN, FEATURE_ADDRESS_MAX + 1)

def read_feature_ids(addresses=None):
    """Generate READ_FEATURE_ID commands."""
    return [ReadFeatureId(address) for address in addresses or FEATURE_ADDRESSES]

def parse_features(ids, commands):
    """Parse READ_FEATURE_ID command responses into a map of features and addresses."""
    addresses = [command.feature_address for command in commands]

    known_ids = {feature.value for feature in Feature}

    features = {}

    for (address, id_) in zip(addresses, ids):
        if id_ is not None and id_ in known_ids:
            feature = Feature(id_)

            features[feature] = address

    return features
