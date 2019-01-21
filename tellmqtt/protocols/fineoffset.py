
from tellmqtt.common import protocoldata as pd
import logging

logger = logging.getLogger(__name__)

class fineoffset:
    def name(self):
        return 'fineoffset'

    def decode(self, msg):
        if not 'data' in msg:
            return None
        vals = dict()
        data = msg['data']

        #skip checksum
        data = data[:-2]

        #read humidity
        hum = int(data[-2:], 16)
        data = data[:-2]

        #read temperature
        tmp = int(data[-3:], 16)
        temp = float(tmp & 0x7ff)
        temp /= 10.0
        if(tmp & 0x800): temp *= -1
        data = data[:-3]

        # read id
        id = int(data, 16) & 0xff

        vals['temperature'] = temp
        # generate string
        if(hum != 0xff):
            vals['humidity'] = hum


        return pd((id,), vals)

