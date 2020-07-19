#!/usr/bin/env python

import sys

from common import create_serial, create_interface

from coax import get_features

with create_serial() as serial:
    interface = create_interface(serial)

    features = get_features(interface)

    print(features)
