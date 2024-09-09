# My CLI + Module Application

## Overview

This application is a flexible CLI and Python module that allows users to configure MQTT and device settings using either a `config.json` file or command-line arguments. It supports nested configurations and provides verbose logging for debugging.

The application is designed to connect to an MQTT broker and interact with a device under test (DUT). The settings for both MQTT and the device can be overridden via the CLI, allowing easy configuration for different environments.

Note: MQTT configuration is included in this version, however real MQTT communication is still missing.

## Features

- **MQTT Configuration**: Host, port, username, and password.
- **Device Configuration**: Device name, port, and timeout.
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
    "device": {
        "name": "Device001",
        "port": "ttyUSB1",
        "timeout": 30
    }
}
```

### 2. Command-Line Arguments

You can override any of the settings from ```config.json``` by passing arguments directly in the CLI. For example:

```python cliapp/cli.py --mqtt-host mqtt.example.com --device-name Device001 --device-port /dev/ttyS0 --verbose```

## Configuration Options

### MQTT Settings

* ```--mqtt-host```: The host of the MQTT broker (default: ```localhost```).
* ```--mqtt-port```: The port to connect to the MQTT broker (default: ```1883```).
* ```--mqtt-username```: The username for MQTT authentication (default: ```guest```).
* ```--mqtt-password```: The password for MQTT authentication (default: ```guest```).

### Device Settings

* ```--device-name```: The name of the device under test (default: ```UnknownDevice```).
* ```--device-port```: The port where the device is connected (default: ```ttyUSB0```).
* ```--device-timeout```: The timeout duration (in seconds) for device connections (default: ```30``` seconds).

General Settings

* ```--verbose```: Enable verbose mode (prints detailed configuration and runtime info).
* ```--no-verbose```: Disable verbose mode (overrides verbose settings from config.json or defaults).

## Usage

### Running the Application

To run the application with default settings or using ```config.json```:

```python cliapp/cli.py```

### Overriding Configuration via Command-Line Arguments

You can override specific settings from ```config.json``` using command-line options:

```python cliapp/cli.py --mqtt-host mqtt.example.com --device-name Device001 --device-port /dev/ttyS0 --verbose```

This command will:

* Connect to the MQTT broker at ```mqtt.example.com```.
* Use ```Device001``` as the name for the device under test.
* Connect to the device via port ```/dev/ttyS0```.
* Enable verbose mode.

### Verbose Mode

Verbose mode provides detailed output, including the final merged configuration and runtime behavior. To enable it:

```python cliapp/cli.py --verbose```

Example:

```python cliapp/cli.py --device-name MyDevice --device-port /dev/ttyUSB2 --mqtt-host mqtt.myserver.com```

Output:

```
MQTT Configuration:
  Host: mqtt.myserver.com
  Port: 1883
  Username: guest
  Password: guest

Device Configuration:
  Device Name: MyDevice
  Port: /dev/ttyUSB2
  Timeout: 30 seconds

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
        "host": "localhost",
        "port": 1883,
        "username": "guest",
        "password": "guest"
    },
    "device": {
        "name": "Device001",
        "port": "ttyUSB0",
        "timeout": 30
    }
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

## License

This project is licensed under the MIT License.
