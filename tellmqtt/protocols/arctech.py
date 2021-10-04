# aka nexa

import json
from tellmqtt.common import protocoldata as pd
import logging

logger = logging.getLogger(__name__)

class arctech:
    def name(self):
        return 'arctech'

    def encode(self, protoarg, command, payload):
        if not protoarg:
            logger.warning("Protocol should be specified")
            return None

        protocol, *options = protoarg
        if protocol == 'selflearning':
            return self.encode_selflearning(options, command, payload)
        if protocol == 'codeswitch':
            return self.encode_codeswitch(options, command, payload)

        logger.warning('no arctech encoder for protocol %r', protocol)
        return None

    def encode_codeswitch(self, options, command, payload):
        logger.debug('codeswitch: encode %r %r=%r', options, command, payload)
        try:
            home, unit = [int(v) for v in options]
        except ValueError:
            logger.warning("Expected options (home, unit), where values are convertible to int")
            return

        if not ((0 <= home <= 0xF) and (0 <= unit <= 0xF)):
            logger.warning("home and unit should be in range [0, 0xF]")
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

        encoded_state = b'$k$k$kk$$kk$$kk$$k+' if state else b'$k$k$kk$$kk$$k$k$k+'
        res = b''.join([b'S', encode_nibble(home), encode_nibble(unit), encoded_state])
        logger.debug("Encoded %r", res)
        return bytearray(res)

    def encode_selflearning(self, options, command, payload):
        logger.debug('selflearning: encode {!r} {!r}={!r}'.format(options, command, payload))
        if(len(options) != 3):
            return None
        try:
            house,group,unit = map(int, options)
        except ValueError:
            logger.warning("selflearning: options not numeric: {}".format('/'.join(options)))
            return None

        if house < 0 or house > 2**26-1 or group < 0 or group > 1 or unit < 1 or unit > 16:
            logger.warning("selflearning: options out of range: {}".format('/'.join(options)))
            return None
        else:
            logger.debug("selflearning: house: {} group: {} unit: {}".format(house, group, unit))

        if payload.upper() == 'ON' or payload.upper() == 'LEARN':
            onoff = 1
        elif payload.upper() == 'OFF':
            onoff = 0
        else:
            logger.warning("selflearning: unsupported command value: {}".format(payload))
            return None

        class buffer:
            def __init__(self):
                self.buf = bytearray([ord('T'), 127,  255, 24, 1])
                self.buf.append(132)
                self.buf.append(0b10011010)
            def codenum(self, num, nbytes):
                for b in range(0, nbytes):
                    v = self.buf.pop() & 0xf0
                    if num & (1 << (nbytes - 1 - b)):
                        self.buf.append(v | 0b1000)
                        self.buf.append(0b10101010)
                    else:
                        self.buf.append(v | 0b1010)
                        self.buf.append(0b10001010)
            def end(self):
                self.buf.append(ord('+'))
                return self.buf

        out = buffer()
        out.codenum(house, 26)
        out.codenum(group, 1)
        out.codenum(onoff, 1)
        out.codenum(unit - 1, 4)
        return out.end()

    def decode(self, msg):
        if(msg['model'] == 'selflearning'):
            return self.decode_selflearning(msg)
        elif msg["model"] == 'codeswitch':
            return self.decode_codeswitch(msg)
        else:
            logger.warning("Model is not supported yet: %r", msg["model"])
            return None

    def decode_selflearning(self, msg):
        data = int(msg['data'], 16)

        house = (data & 0xffffffc0) >> 6
        group = (data & 0x20) >> 5
        unit = (data & 0xf) + 1

        if data & 0x10:
            method = 'ON'
        else:
            method = 'OFF'

        return pd((msg['model'],house,group,unit), {'set': method})

    def decode_codeswitch(self, msg):
        data = int(msg['data'], 16)
        if data == 0:
            return None
        house = (data & 0xf)
        unit = (data >> 4) & 0xf
        method = 'ON' if (data & 0x800) else 'OFF'
        return pd((msg["model"], house, unit), {"set": method})
