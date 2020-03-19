"""
coax.interface
~~~~~~~~~~~~~~
"""

class Interface:
    def reset(self):
        raise NotImplementedError

    def transmit(self, words, repeat_count=None, repeat_offset=1):
        raise NotImplementedError

    def receive(self, length=None, timeout=None):
        raise NotImplementedError

    def transmit_receive(self, transmit_words, transmit_repeat_count=None,
                         transmit_repeat_offset=1, receive_length=None,
                         receive_timeout=None):
        raise NotImplementedError
