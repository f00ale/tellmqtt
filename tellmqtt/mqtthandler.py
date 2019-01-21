import logging
import asyncio
import functools

logger = logging.getLogger(__name__)
asciibytes = functools.partial(bytes, encoding='ascii')

class MqttHandler:
    def createpost(self, msg):
        path = 'tellstick/in/'+'/'.join(map(str, msg.path))
        return [(path+'/'+str(k),asciibytes(str(v))) for (k,v) in msg.values.items()]

    def decodepost(self, topic, payloadba):
        fullpath = tuple(topic.split('/'))
        # assume first is ('tellstick','out') for now
        protocol = fullpath[2]
        arguments = fullpath[3:-1]
        command = fullpath[-1]
        payload = payloadba.decode('utf-8')
        logger.debug("protocol: {!r} arguments: {!r} command: {!r} data: {!r}".format(protocol, arguments, command, payload))
        return (protocol, arguments, command, payload)
