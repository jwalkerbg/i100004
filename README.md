# My CLI + Module Application

## Overview

This application is a flexible CLI and Python module that allows users to configure MQTT and MS protocol settings using either a `config.json` file or command-line arguments. It supports nested configurations and provides verbose logging for debugging.

The application is designed to connect to an MQTT broker and interact with a server under test (DUT). The settings for both MQTT and the device can be overridden via the CLI, allowing easy configuration for different environments.

Note: MQTT configuration is included in this version, however real MQTT communication is still missing.

## Features

- **MQTT Configuration**: Host, port, username, and password.
- **MS Protocol**: Client and server MAC addresses, MQTT topics etc
- **Command-Line Overrides**: You can override configuration values specified in `config.json` directly from the command line.
- **Verbose Mode**: The application can run in verbose mode to provide detailed logging of the configuration and runtime behavior.

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

## Extending the Application

You can easily extend this application by adding more configuration options in the ```config.json``` file or expanding the CLI to accept additional arguments.

To add a new configuration section:

1. Update the ```DEFAULT_CONFIG``` in config.py.
2. Modify the schema in ```config.py``` to validate the new options.
3. Update the CLI parser in ```cli.py``` to accept new options.
4. Modify the run_app function in ```core.py``` to make use of the new options.

## Contributing

Feel free to fork this project and submit pull requests. All contributions are welcome!

## How to make importable module



## License

This project is licensed under the MIT License.
