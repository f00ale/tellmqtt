# aka Clas Ohlson

import json
from tellmqtt.common import protocoldata as pd
import logging

logger = logging.getLogger(__name__)

class mandolyn:
    def name(self):
        return 'mandolyn'

    def decode(self, msg):
        if not 'data' in msg:
            return None

        vals = dict()

        data = int(msg['data'], 16)

        # parity
        parity = data & 0x1
        data >>= 1

        # temperature
        temp = ((data & 0x7FFF) - 6400) / 128
        temp = round(temp, 1)
        data >>= 15

        # humidity
        humidity = data & 0x7F
        data >>= 7

        # battery
        battery = data & 0x1
        data >>= 3

        # channel
        channel = (data & 0x3) + 1
        data >>= 2
   
        # house
        house = data & 0xF

        # create id
        # channel range: 1 - 4
        # house range: 1 - 15
        id = channel * 100 + house

        # set values
        vals['temperature'] = temp
        vals['humidity'] = humidity
        vals['battery'] = battery
        vals['house'] = house
        vals['channel'] = channel
        vals['parity'] = parity
      
        return pd((id,), vals)
