#!/usr/bin/env python

from common import open_example_serial_interface

from coax import get_features

with open_example_serial_interface() as interface:
    features = get_features(interface)

    print(features)
