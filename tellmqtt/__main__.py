import logging
import asyncio
import serial_asyncio

from amqtt.client import MQTTClient
from amqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

import tellmqtt
import tellmqtt.tellstickhandler
import tellmqtt.mqtthandler

import tellmqtt.fake.serial as fake_serial

import argparse

logger = logging.getLogger('tellmqtt')

def getopt():
    parser = argparse.ArgumentParser(add_help=False) # no add_help as we want -h for host
    parser.add_argument('--help', action="help", help="Show help message and exit.")
    parser.add_argument('-h', '--host',
                        dest="mqtthost", default="localhost",
                        help="MQTT broker host. Default: %(default)s")
    parser.add_argument('-p', '--port',
                        dest="mqttport", default=1883,
                        help="MQTT broker port. Default: %(default)s")

    parser.add_argument('-d', '--device',
                        dest="device", default="/dev/tellstickDuo",
                        help="Tellstick device. Default: %(default)s")

    args = parser.parse_args()
    return args

def serial_setup(loop, args):
    if args.device != 'fake':
        return serial_asyncio.open_serial_connection(loop=loop, url=args.device, baudrate=9600)
    else:
        return fake_serial.open_serial_connection()

def mqtt_setup(loop, args):
    client = MQTTClient()
    return client, client.connect('mqtt://{}:{}/'.format(args.mqtthost, args.mqttport))

async def readproc(serialread, mqttclient, mqtt, stick, ready):
    while True:
        rawline = await serialread.readline()
        ret = stick.decode(rawline)
        if ret:
            outs = mqtt.createpost(ret)
            for (path,data) in outs:
                logger.debug("{!r} -> {!r}".format(path,data))
            tasks = [
                asyncio.ensure_future(mqttclient.publish(path, data)) for (path,data) in outs
            ]
            await asyncio.wait(tasks)
        else:
            ready.set()

_PINGED = False

async def ping(mqttclient):
    global _PINGED
    while True:
        if not _PINGED:
            logger.info("Re-subscribe")
            await mqttclient.subscribe([('tellstick/out/#', QOS_0)])
            await mqttclient.subscribe([('tellstick/ping', QOS_0)])
        await asyncio.sleep(30)
        _PINGED = False
        await mqttclient.publish("tellstick/ping", b'')
        await asyncio.sleep(30)

async def writeproc(serialwrite, mqttclient, mqtt, stick, ready):
    global _PINGED
    while True:
        message = await mqttclient.deliver_message()
        packet = message.publish_packet
        dec = mqtt.decodepost(packet.variable_header.topic_name, packet.payload.data)
        if dec == 'ping':
            _PINGED = True
            continue
        logger.debug('decoded to {!r}'.format(dec))
        out = stick.encode(*dec)
        if out:
            logger.debug('write {!r}'.format(out))
            await ready.wait()
            serialwrite.write(out + b'\n')
            ready.clear()
        else:
            logger.debug('no output')

async def main(loop, opts):
    try:
        client, co = mqtt_setup(loop, opts)
        await co
    except:
        logger.critical("Error connecting to MQTT broker")
        return

    try:
        r,w = await serial_setup(loop, opts)
    except Exception as e:
        logger.critical("Error opening tellstick device: {!r}".format(e))
        await client.disconnect()
        return

    stickhandler = tellmqtt.tellstickhandler.TellstickHandler()
    mqtthandler = tellmqtt.mqtthandler.MqttHandler()

    # kludge: use ackevent to signal that the stick is ready for another command.
    # to be rewritten.
    ackevent = asyncio.Event()
    ackevent.set()

    await asyncio.gather(
        readproc(r, client, mqtthandler, stickhandler, ackevent),
        writeproc(w, client, mqtthandler, stickhandler, ackevent),
        ping(client),
    )

    await client.disconnect()

def setup_logging():
    logging.disable(logging.NOTSET)
    logging.basicConfig(
        datefmt='[%Y-%m-%dT%H:%M:%S%z]',
        format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    )
    logger.setLevel(logging.INFO)

if __name__ == '__main__':
    setup_logging()
    opts = getopt()
    logger.debug("starting")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop, opts))
    loop.close()
