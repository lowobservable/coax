#!/usr/bin/env python

from common import open_example_serial_interface

from coax import read_feature_ids, parse_features

with open_example_serial_interface() as interface:
    commands = read_feature_ids()

    ids = interface.execute(commands)

    features = parse_features(ids, commands)

    print(features)
