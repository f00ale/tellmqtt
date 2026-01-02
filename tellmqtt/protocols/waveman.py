"""
Protocol for waveman

Tested models:
 - Waveman Codeswitch, article no 17.356
"""

import json
from tellmqtt.common import protocoldata as pd
import logging

logger = logging.getLogger(__name__)

class waveman:
    def name(self):
        return 'waveman'

    def encode(self, protoarg, command, payload):
        if not protoarg:
            logger.warning("Protocol should be specified")
            return None

        protocol, *options = protoarg
        logger.debug('codeswitch: encode %r %r=%r', options, command, payload)

        if protocol != 'codeswitch':
            logger.warning('no waveman encoder for protocol %r', protocol)
            return None

        try:
            house, unit = options
            if ord(house) >= ord('A'):
                house = ord(house.upper()) - ord('A')
                unit = int(unit) - 1
            else: # for arctech codeswitch compatibility
                house = int(house)
                unit = int(unit)
        except ValueError:
            logger.warning("Expected options (house, unit), where values are convertible to int")
            return

        if not ((0 <= house <= 0xF) and (0 <= unit <= 0xF)):
            logger.warning("house and unit should be in range [0, 0xF]")
            return

        states = {'ON' : True, 'OFF': False, '0': False, '1': True}
        try:
            state = states[payload.upper()]
        except (KeyError, TypeError) as err:
            logger.warning("Payload should have one of the following values: %s. Error: %r", ", ".join(states.keys()), err)
            return

        def encode_nibble(t):
            one, zero = b'$kk$', b'$k$k'
            return b''.join(one if (t >> i & 1) else zero for i in range(4))

        encoded_state = b'$k$k$kk$$kk$$kk$$k+' if state else b'$k$k$k$k$k$k$k$k$k+'
        res = b''.join([b'S', encode_nibble(house), encode_nibble(unit), encoded_state])
        logger.debug("Encoded %r", res)
        return bytearray(res)

    def decode(self, msg):
        if msg["model"] == 'codeswitch':
            data = int(msg['data'], 16)
            if data == 0:
                return None
            house = (data & 0xf)
            unit = (data >> 4) & 0xf
            method = 'ON' if (data & 0x800) else 'OFF'
            return pd((msg["model"], house, unit), {"set": method})
        else:
            logger.warning("Model is not supported yet: %r", msg["model"])
            return None
