# MQTTMS

- [MQTTMS](#mqttms)
  - [Overview](#overview)
  - [Project organization](#project-organization)
    - [Build](#build)
  - [Structure](#structure)
  - [Configuration](#configuration)
    - [1. `config.json` File](#1-configjson-file)
    - [2. Command-Line Arguments](#2-command-line-arguments)
  - [Configuration Options](#configuration-options)
    - [MQTT Settings](#mqtt-settings)
    - [MS Protocol Settings](#ms-protocol-settings)
  - [Usage](#usage)
    - [Running the Application](#running-the-application)
    - [Overriding Configuration via Command-Line Arguments](#overriding-configuration-via-command-line-arguments)
    - [Verbose Mode](#verbose-mode)
    - [Requirements](#requirements)
  - [Configuration File](#configuration-file)

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
+--------------+-----------------+
| MS protocol  | Other module(s) |
+--------------+-----------------+
|         MQTT Disptacher        |
+--------------------------------+
|          MQTT Handler          |
+--------------------------------+
|        mqtt-paho library       |
+--------------------------------+
```

## Configuration

The application can be configured in two ways:
1. Using a `config.json` file.
2. Overriding specific values using command-line arguments.

### 1. `config.json` File

By default, the application looks for a `config.json` file in the current directory. This file should contain the configuration settings for both MQTT and the device. Here's an example of the structure:

```json
{
    "mqtt": {
        "host": "mqtt.example.com",
        "port": 1883,
        "username": "user",
        "password": "pass"
    },
}
```

### 2. Command-Line Arguments

You can override any of the settings from ```config.json``` by passing arguments directly in the CLI. For example:

```python mqttms/cli.py --mqtt-host mqtt.example.com --verbose```

## Configuration Options

### MQTT Settings

* ```--mqtt-host```: The host of the MQTT broker (default: ```localhost```).
* ```--mqtt-port```: The port to connect to the MQTT broker (default: ```1883```).
* ```--mqtt-username```: The username for MQTT authentication (default: ```guest```).
* ```--mqtt-password```: The password for MQTT authentication (default: ```guest```).

### MS Protocol Settings

* ```client_mac```: Client MAC address without separators (':' or '-')
* ```server_mac```: Server (slave) MAC address without separators (':' or '-')
* ```cmd_topic```: MQTT topic template for commands
* ```rsp_topic```: MQTT topic template for responses
* ```timeout```: MS Protocol timeout in seconds (float number)


General Settings

* ```--verbose```: Enable verbose mode (prints detailed configuration and runtime info).
* ```--no-verbose```: Disable verbose mode (overrides verbose settings from config.json or defaults).

## Usage

### Running the Application

To run the application with default settings or using ```config.json```:

```python mqttms/cli.py```

### Overriding Configuration via Command-Line Arguments

You can override specific settings from ```config.json``` using command-line options:

```python mqttms/cli.py --mqtt-host mqtt.example.com --verbose```

This command will:

* Connect to the MQTT broker at ```mqtt.example.com```.
* Enable verbose mode.

### Verbose Mode

Verbose mode provides detailed output, including the final merged configuration and runtime behavior. To enable it:

```python mqttms/cli.py --verbose```

Example:

```python mqttms/cli.py --mqtt-host mqtt.myserver.com```

Output:

```
MQTT Configuration:
  Host: mqtt.myserver.com
  Port: 1883
  Username: guest
  Password: guest

Application started with the above configuration...
```

### Requirements

* Python 3.x
* Install dependencies by running:

```pip install -r requirements.txt```

## Configuration File

If you need to use a different ```config.json``` file, you can create a ```config.json``` with the following structure:

```json
{
    "mqtt": {
        "host": "broker.emqx.io",
        "port": 1883,
        "username": "",
        "password": "",
        "client_id": "client_394578",
        "timeout": 30.0,
        "long_payload": 25
    },
    "ms": {
        "client_mac": "1234567890A1",
        "server_mac": "F412FACEF2E8",
        "cmd_topic": "@/server_mac/CMD/format",
        "rsp_topic": "@/client_mac/RSP/format",
        "timeout": 5.0
    },
    "verbose": false
}
```

The application will load this file at runtime unless overridden by command-line arguments.

