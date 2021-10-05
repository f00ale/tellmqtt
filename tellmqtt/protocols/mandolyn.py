"""
Protocol for mandolyn

Tested models:
 - ESIC WT450H (Clas Ohlson)
"""

import logging

from tellmqtt.common import protocoldata as pd

logger = logging.getLogger(__name__)


class mandolyn:
    """
    Mandolyn Protocol
    """

    def __init__(self):
        self.protocol = 'mandolyn'

    def name(self):
        """
        Name of protocol
        """
        return self.protocol

    @staticmethod
    def decode(msg):
        """
        Decode data and return temperature, humidity and battery status
        """
        if not 'data' in msg:
            return None

        data = int(msg['data'], 16)

        # parity (unused)
        # parity = data & 0x1
        data >>= 1

        # temperature
        temperature = ((data & 0x7FFF) - 6400) / 128
        temperature = round(temperature, 1)
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

        # set values
        vals = {}
        vals['temperature'] = temperature
        vals['humidity'] = humidity
        vals['battery'] = battery

        return pd((channel, house), vals)
