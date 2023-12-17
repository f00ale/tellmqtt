from tellmqtt.common import protocoldata as pd
import functools
import logging

logger = logging.getLogger(__name__)

# CRC method is deduced from sample data gather from Telldus sensors using
# https://reveng.sourceforge.io/
#
# width=8 poly=0x31 init=0x00 refin=false refout=false xorout=0x00 check=0xa2
# residue=0x00 name=(none)

@functools.cache
def get_crc_tbl():
    tbl = []

    for crc in range(256):
        for _ in range(8):
            msb_set = crc & 0x80
            crc = (crc << 1) & 0xff
            if msb_set:
                crc ^= 0x31
        tbl.append(crc)

    return tbl


def calc_crc(data: bytes) -> int:
    tbl = get_crc_tbl()
    crc = 0
    for byte in data:
        idx = crc ^ byte
        crc = (crc << 8) & 0xff
        crc ^= tbl[idx]

    return crc

as_int = functools.partial(int.from_bytes, byteorder="big")

class fineoffset:
    def name(self):
        return 'fineoffset'

    def decode(self, msg):
        data = msg.get('data')
        if data is None:
                return None

        if len(data) != 10:
            # see https://github.com/telldus/telldus/blob/master/telldus-core/service/ProtocolFineoffset.cpp
            logger.warning("Expected format is _[0:7], ID[8:11], T[12:23], H[24:31], CRC[32:39], got %s", data)
            return None

        data_bytes = bytes.fromhex(data)
        crc = data_bytes[-1]
        if calc_crc(data_bytes[:-1]) != crc:
            logger.warning("Got corrupted data, skipping: '%s'", data)
            return None

        vid, temp, hum = int(data[:3], 16), int(data[3:6], 16), int(data[6:8], 16)

        res = {
            "temperature": (temp & 0x7ff) / (-10.0 if temp & 0x800 else 10.0),
        }
        if hum <= 100:
            res['humidity'] = hum

        return pd((vid,), res)
