# MQTTMS

- [MQTTMS](#mqttms)
  - [Overview](#overview)
  - [Project organization](#project-organization)
    - [Build](#build)
  - [Structure](#structure)
  - [Configuration](#configuration)
    - [MQTTMS configuration](#mqttms-configuration)
    - [Logging configuration.](#logging-configuration)
    - [Example of supplying configuration options.](#example-of-supplying-configuration-options)
  - [Classes](#classes)
    - [class MQTTms.](#class-mqttms)
      - [`__init__`](#__init__)
      - [`connect_mqtt_broker`](#connect_mqtt_broker)
      - [`subscribe`](#subscribe)
      - [`graceful_exit`](#graceful_exit)

## Overview

MQTTMS implements basic MQTT client plus support for MS (Master-Slave) protocol, master side. I can be used by applications which provide it with connection and subscription information about MQTT. Also, applications provide information to configure MS protocol (format of MQTT topics, etc). Once configured, the module can be used by applications to send commands to devices over MQTT and receive back information from them.

The module is constructed to run MS protocol. However besides it, application can bet set to run other MQTT communications as well.

## Project organization

MQTTMS uses `pyproject.toml` organization. It does not use old and obsolete `setup.py` or `requrements.txt` files.

### Build

The project can be built from source by executing

`python -m build`

from the root diretory of the project. (Module `build` must be installed before that by `pip install build`.)

This will produce two files in `dist` directory:

* mqttms-1.1.0-py3-none-any.whl
* mqttms-1.1.0.tar.gz

These files can be distrubuted and installed by

`pip install mqttms-1.1.0-py3-none-any.whl`

or

`pip install mqttms-1.1.0.tar.gz`

One of these is enough, and `whl` is preferred. For developing, the repository with the sources can be used and installed in editable mode by

`pip install -e .`

As this module cannot be used alone, an application is needed to use it, the better scenario is to create common virtual environment of MQTTMS and the application and then install the module with above command in this common envronment.

## Structure

MQTTMS has layered structure.

```
+--------------------------------+
|          Application           |
+================================+---
|            MQTTms              |m
|--------------+-----------------|q
| MS protocol  |      Logger     |t
+--------------+-----------------+t
|         MQTT Disptacher        |m
+--------------------------------+s
|          MQTT Handler          |
+================================+---
|        mqtt-paho library       |
+--------------------------------+
```

`mqtt-paho-library` is external module `paho-mqtt`.

MQTT Handler (`class MQTTHandler`) handles communications with MQTT broker. Operations on connection, subscritions, disconnection, receiving and publishing messages is its job. This class has two threads, one for receiving and one for publishing. This way it allows asynchronous work in the sytsem it is used in. `MQTTHandler` works with MQTT Disptacher for received messages. The communication is through a callback function with dedicated name `handle_message`, part of MQTT Disptacher.

MQTT Disptacher (`MQTTDispatcher`) is a class that distrbutes received messages among eventual receivers. The main function of interest is `handle_message`. It receives a tuple of two strings, the MQTT topic and payload. Note: if the payload represents a json, it is a string representation of the json object, not the json object itself.

The default implementation `MQTTDispatcher.handle_message` recognizes the messages intened to MS protocol. If other messages are to be recognized for other receivers, `class MQTTDispatcher` should be inherited by another class that implements its own `handle_message` function.

MS Protocol (`class MSProtocol`) is an implementation of MS protocol, host (master) side. It can communicate with slave side by sending commands and receiving answers. It uses `class MQTTHandler` to publish commands. Then `class MQTTHandler` uses `class MQTTDispatcher` to dispatch respones to `class MQTTHandler`.

The main class of `mqttms` module is `class MQTTms`. It creates objects of above classes and creates links between them.

## Configuration

To work, `mqttms` must be supplied with configuration for `MQTTHandler` and for `MSProtocol`. This is done through the arguments of the constructor of `MQTTms` object. The configurations are `Dict` objects: one for MQTT Handler and MS Protocol and otyher of logger verbosity.

### MQTTMS configuration

MQTTMS configuration is as follows (real example):

```python
'mqttms': {
    'mqtt': {
        'host': 'broker.emqx.io',
        'port': 1883,
        'username': '',
        'password': '',
        'client_id': 'mqttx_93919c20',
        "timeout": 15.0,
        "long_payload": 25
    },
    'ms': {
        'client_mac': '1234567890AB',
        'server_mac': '112233445566',
        'cmd_topic': '@/server_mac/CMD/format',
        'rsp_topic': '@/client_mac/RSP/format',
        'timeout': 5.0
    }
}
```

Here, it is divided to two parts - `mqtt` for MQTT Handler and `ms` for MS Protocol.

`mqtt.host` and `mqtt.port` determine MQTT broker, `mqtt.username` and `mqtt.password` are empty if not used, otherwise they have to be valid credentials for the broker. `mqtt.timeout` is the time in seconds to wait for reaction from the MQTT broker after connecting, subscribing, disconnecting and so on.

`mqtt.long_payload` is a constant used by the logger. If the payload is longer than this value the logger prints 'long payload' instead of the payload. This happens if `logging.verbose` is `False`.

`ms.client_mac` is the MAC address of the device that runs this module with MS protocol host side. `ms.server_mac` is the MAC address of the slave device that receives command and returns respones to the client. These are parts of topics and subscriptions so as the host (client) and the slave (server) know each other.

`ms.cmd_topic` determines the format of topics of the commands. `ms.rsp_topic` determines the format of the responces. The slave (server) subscribes for `ms.cmd_topic` and the host (client) subscribes for `ms.rsp_topic`. `ms.client_mac` also travels as a field in command payloads (added automatically, application programmer do not need to worry about it).

'ms.timeout` is the time in seconds for waiting responses of published commands.

### Logging configuration.

Logging configuration is simple. In current version, it determines whether the logging will be verbose or not (`True` or `False`).

```python
'logging': {
    'verbose': False
}
```

### Example of supplying configuration options.

Above configurations are given as JSON objects. They are supplied as aruments of creating `MQTTms` object. Example:

```config``` is a `Dict` object which have in itself sub-objects `mqttms` and `logging`.

```python
    # create object
    try:
        mqttms = MQTTms(config['mqttms'],config['logging'])
    except Exception as e:
        logger.error(f"Cannot create MQTTMS object. Giving up: {e}")
        return
```

## Classes

### class MQTTms.

`class MQTTms` is the main (root) class. Creation of an object ofthis class creates all needed internal objects, threads, connections between objects.

Member functions

#### `__init__`

Prototype:

```
__init__(self, config:Dict, logging:Dict, mqtt_dispatcher: MQTTDispatcher=None)
```

Parameters:
* `config:Dict` - confguration options supplied by the application used `mqttms`.
* `logging:Dict` - configuration options of logging supplied by the application used `mqttms`.
* `mqtt_dispatcher: MQTTDispatcher=None` - dispatcher object. If none, default dispatcher object is used, that dispatched MS protocol responces

`config:Dict` is a JSON structure that should meet following validation schema

```
{
    "mqttms": {
        "type": "object",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "properties": {
            "mqtt": {
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                    "client_id": {"type": "string"},
                    "timeout": {"type": "number"},
                    "long_payload": {"type": "integer", "minimum": 10, "maximum": 32768}
                },
                "required": ["host", "port"]
            },
            "ms": {
                "type": "object",
                "properties": {
                    "client_mac": {"type": "string"},
                    "server_mac": {"type": "string"},
                    "cmd_topic": {"type": "string"},
                    "rsp_topic": {"type": "string"},
                    "timeout": {"type": "number"}
                },
                "required": ["client_mac", "server_mac", "cmd_topic", "rsp_topic", "timeout"]
            }
        },
        "required": ["mqtt", "ms"],
        "additionalProperties": False
    }

}
```
As it can be seen this data is used to configure MQTT Handler and MS protocol.

`logging:Dict` is a JSON structure that should meet following validation schema

```
{
    "logging": {
        "type": "object",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "properties": {
            "verbose": {
                "type": "boolean"
            }
        },
        "additionalProperties": False
    }
}
```

It configures the logger module. Now, to be verbose or not.

`mqtt_dispatcher: MQTTDispatcher=None` supplies `MQTTDispather` object. If this argument is ommited (is `None`), then the default dispatcher is used from mqttms. However the caller (the application) can define other dispather that probablydisptaches many kind of messages and supply here as an argument.

#### `connect_mqtt_broker`

Prototype:

```
connect_mqtt_broker(self) -> bool
```

This function tries to connect to the broker which data (uri, port) are given as a part of `config` parameter on initializing `MQTTms` object. It is a blocking function. It returns `True` after successful connection and `False` on fail.

#### `subscribe`

Prototype:

```
subscribe(self) -> bool
```

This function subscribes the client to the topic, given in the confioguration, in "ms" section - the responce of MS protocol commands. There is no way in currentr version to create additional subscriptions with this function. If they are needed, this can be done through `self.mqtt_handler` member object.

#### `graceful_exit`

Prototype:

```
graceful_exit(self) -> None:
```

This function executes chain of actions to terminate threads and disconnect from the server. It tries to terminate in grasefull way not hanging and not leaving some threads working.
