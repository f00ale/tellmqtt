import logging

from tellmqtt.common import protocoldata as pd

from tellmqtt.protocols.fineoffset import fineoffset
from tellmqtt.protocols.arctech import arctech

import json

logger = logging.getLogger(__name__)

PROTOCOLS = [
    arctech(),
    fineoffset(),
]

class TellstickHandler:
    def __init__(self):
        self.decoders = dict()
        self.encoders = dict()
        for proto in PROTOCOLS:
            name = proto.name()
            if hasattr(proto, 'decode'):
                self.decoders[name] = proto
            if hasattr(proto, 'encode'):
                self.encoders[name] = proto

    def itemize(self, raw):
        msg = raw.translate(None, b'\r\n')
        lst = msg.split(b';')
        ret = {}
        for i in lst:
            if i != b'':
                [a,b] = i.split(b':')
                ret[a.decode('ascii')] = b.decode('ascii')
        return ret


    def decode(self, b):
        if b.startswith(b'+W'):
            d = self.itemize(b[2:])
        elif b.startswith(b'+T'):
            return None # ack on command
        else:
            logger.warning('unknown input {!r}'.format(b))
            return None

        if 'protocol' in d:
            protname = d['protocol']
        else:
            logger.warning('protocol field not found in {!r}'.format(b))
            return None

        if protname in self.decoders:
            ret = self.decoders[protname].decode(d)
        else:
            logger.warning('no decoder for protocol {}'.format(protname))
            return None

        if ret is not None:
            if not 'json' in ret.values.keys():
                ret.values['json'] = json.dumps(ret.values, sort_keys=True, separators=(',', ':'))

            return pd((protname,)+ret.path, ret.values)
        else:
            return None

    def encode(self, protocol, protoargs, command, value):
        if protocol in self.encoders:
            logger.debug('calling encode for protocol {}'.format(protocol))
            try:
                return self.encoders[protocol].encode(protoargs, command, value)
            except Exception as e:
                logger.critical(repr(e))
                return None
        else:
            logger.warning('no encoder for protocol {}'.format(protocol))
            return None

