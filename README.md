# tellmqtt

This program acts as a bridge between a USB-connected tellstick and 
a mqtt-server, written with python3.

Currently only the Telldus Tellstick Duo is supported.

The MQTT interface is rather raw, incoming data is decoded and published
under `tellstick/in/<protocolname>/<protocoldetails>` while for sending 
data out post a message to `tellstick/out/<protocolname>/<details>` 

## Usage
### Hardware setup
This program needs the tellstick to show up as an ordinary serial port.
This is done with the linux kernel module `ftdi_sio`. However the 
module does not recognize the tellstick out of the box, so some special 
commands are needed (as root):
```
# modprobe ftdi_sio
# echo 1781 0c31 > /sys/bus/usb-serial/drivers/ftdi_sio/new_id
```
After this the kernel log should show something like
```
usbcore: registered new interface driver ftdi_sio
usbserial: USB Serial support registered for FTDI USB Serial Device
ftdi_sio 2-2:1.0: FTDI USB Serial Device converter detected
usb 2-2: Detected FT232RL
usb 2-2: FTDI USB Serial Device converter now attached to ttyUSB0
```

The final `ttyUSB0` shows which device file under `/dev/` was created.

The docs-directory contains a udev rule file (`90-tellstick.rules`) 
which can be used to do this automatically, it also creates a symlink
`/dev/tellstickDuo` to the device and sets permissions so the `plugdev` group
can use it.

### Software setup
I recommend using a python virtual environment, with at least python 3.6:
```
$ cd <tellmqtt main directory>
$ python3 -m virtualenv -p python3 venv
$ . venv/bin/activate
$ pip3 install $(cat requirements.txt)
$ python3 -m tellmqtt -d /dev/tellstickDuo -h mqtt-server
```

### Running tellmqtt
Using the previously created device symlink and virtual environment 
tellmqtt can be started with:
```
$ cd <tellmqtt main directory>
$ . venv/bin/activate
$ python3 -m tellmqtt -d /dev/tellstickDuo -h mqtt-server
```

**NB!** Please do not run tellmqtt as root!

## Tested devices (protocols)
### Fineoffset
#### Telldus Termo- and hygrometer
Models FT007TH, F007TPH

The following topics are published:

`tellstick/in/fineoffset/<channel>/temperature` temperature

`tellstick/in/fineoffset/<channel>/humidity` humidity (if applicable)

`tellstick/in/fineoffset/<channel>/json` all data in a json structure (useful if logging to database)

The termo-/hygrometers have dipswitches to set the channel 1-8

The protocol-level channel is calculated as the set number * 16 + 119. So channel 1 becomes 135, channel 2 151 and so on.

For the combined indoor/outdoor sensor (F007TPH) the outdoor temperature is on channel 120 + ch * 16 (no humidity for outdoor).

### Arctech self-learning
The arctech self-learning protocol reads/writes to 
`tellstick/(in/out)/arctech/selflearning/<house>/<group>/<unit>/set`

where

`<house>` is a number 0 - 67108863

`<group>` is 0 or 1

`<unit>` is 1 - 16

The value of the topic on input can be either `on` or `off` (case insensitive).
On output also the value `learn` can be given to learn a new code (provided that the receiver is in learning mode)

#### Telldus remote control
Model EWT0006

The remote has 4 on/off buttons: 1, 2, 3 and G

The house-code is hardcoded per device. To find it out use 
`mosquitto_sub -v -t tellstick/in/\#` and press the buttons (or use another mqtt subscriber)

Then group/unit is used as:

1: 0/16

2: 0/15

3: 0/14

G: 1/16

#### Nexa doorbell button
This works a lot like the Telldus remote control, but it only send an `ON` signal
with group = 1, unit = 1.

#### Telldus power-switch
Models EWR1003 and 312538

1. Decide on a valid combination of house, group and unit codes 
2. Set your receiving device in learning mode
3. send `LEARN` to `/tellstick/out/arctech/selflearning/<house>/<group>/<unit>/set`

Then send `ON`/`OFF` to `/tellstick/out/arctech/selflearning/<house>/<group>/<unit>/set`
to turn the switch on/off.

#### Nexa doorbell
Follow the telldus power-switch instructions. Note that the doorbell only listens to the `LEARN` and `ON`
commands.

## HomeAssistant examples
Here are examples on how to use tellmqtt with HomeAssistant and its mqtt-support.
### Indoor/outdoor temperature/humidity sensor
Sensor with ID set to 2:
```yaml
sensor:
  - platform: mqtt
    state_topic: "tellstick/in/fineoffset/151/temperature"
    name: "Indoor temperature"
    device_class: "temperature"
    unit_of_measurement: '°C'
  - platform: mqtt
    state_topic: "tellstick/in/fineoffset/151/humidity"
    name: "Indoor humidity"
    device_class: "humidity"
    unit_of_measurement: '%'
  - platform: mqtt
    state_topic: "tellstick/in/fineoffset/152/temperature"
    name: "Outdoor temperature"
    device_class: "temperature"
    unit_of_measurement: '°C'
```

### Telldus remote control
```yaml
binary_sensor:
  - platform: mqtt
    state_topic: "tellstick/in/arctech/selflearning/123/0/16/set"
    name: "Remote 1"
  - platform: mqtt
    state_topic: "tellstick/in/arctech/selflearning/123/0/15/set"
    name: "Remote 2"
  - platform: mqtt
    state_topic: "tellstick/in/arctech/selflearning/123/0/14/set"
    name: "Remote 3"
  - platform: mqtt
    state_topic: "tellstick/in/arctech/selflearning/123/1/16/set"
    name: "Remote G"

```
Replace `123` with the house code of your remote control.

### Power switch
```yaml
switch:
  - platform: mqtt
    command_topic: "tellstick/out/arctech/selflearning/456/0/1/set"
    name: "Powerswitch"
```
Replace `456/0/1` with the house, group and unit codes of your switch

TellStick is a trademark of Telldus Technologies AB
