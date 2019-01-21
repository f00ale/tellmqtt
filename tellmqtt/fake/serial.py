import asyncio
import logging

logger = logging.getLogger(__name__)

def open_serial_connection():
    async def fun():
        class fakereader:
            idx = 0
            rets = [
                b'+Wclass:sensor;protocol:fineoffset;data:4970D82884;\r\n',
                b'+Wclass:sensor;protocol:fineoffset;data:49881FFFBB;\r\n',
                b'+Wclass:sensor;protocol:fineoffset;data:49801AFF9E;\r\n',
                b'+Wprotocol:arctech;model:selflearning;data:0x8C42D49E;\r\n'

            ]
            async def readline(self):
                await asyncio.sleep(15)
                self.idx += 1
                if self.idx >= len(self.rets): self.idx = 0
                return self.rets[self.idx]
        class fakewriter:
            def write(self, data):
                logger.debug('write {!r}'.format(data))

        return fakereader(),fakewriter()
    return fun()
