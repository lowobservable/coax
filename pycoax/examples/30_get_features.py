#!/usr/bin/env python

from common import open_example_serial_interface

from coax import read_feature_ids, parse_features

with open_example_serial_interface() as interface:
    commands = read_feature_ids()

    ids = interface.execute(commands)

    for (a, b) in zip(commands, ids):
        print('{0:1X}'.format(a.feature_address) + ' => ' + ('{0:2X}'.format(b) if b is not None else '-'))

    features = parse_features(ids, commands)

    print(features)
