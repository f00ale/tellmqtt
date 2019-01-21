# aka nexa

import json
from tellmqtt.common import protocoldata as pd
import logging

logger = logging.getLogger(__name__)

class arctech:
    def name(self):
        return 'arctech'

    def encode(self, protoarg, command, payload):
        if(len(protoarg) > 0 and protoarg[0] == 'selflearning'):
            return self.encode_selflearning(protoarg[1:], command, payload)
        else:
            logger.warning('no arctech encoder for protocol {}'.format(protoarg[0]))
            return None

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
        else:
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
