import time
import argparse
from coax import open_serial_interface

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('serial_port', help='Serial port')

    args = parser.parse_args()

    with open_serial_interface(args.serial_port) as interface:
        interface.enter_dfu_mode()

        # Wait for the interface to restart in DFU mode.
        time.sleep(3)

        print('Interface should now be in DFU mode...')

if __name__ == '__main__':
    main()
