"""
coax.features
~~~~~~~~~~~~~
"""

from enum import Enum

from .protocol import read_feature_id

class Feature(Enum):
    """Terminal feature."""

    EAB = 0x79

def get_features(interface, **kwargs):
    """Get the features a terminal supports."""
    known_ids = set([feature.value for feature in Feature])

    features = dict()

    for address in range(2, 16):
        id_ = read_feature_id(interface, address, **kwargs)

        if id_ is not None and id_ in known_ids:
            feature = Feature(id_)

            features[feature] = address

    return features
