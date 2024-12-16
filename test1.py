from typing import Dict, Tuple, Any
import json
from jsonschema import validate, ValidationError

DEFAULT_CONFIG: dict = {
    'logging': {
        'verbose': False
    },
    'mqttms': {
        'mqtt': {
            'host': 'localhost',
            'port': 1883,
            'username': 'guest',
            'password': 'guest',
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
}

config: dict = {
    "logging" : {},
    "mqttms" : {}
}

mqttms = DEFAULT_CONFIG['mqttms']

config['mqttms'].update(mqttms)

loggingdict = DEFAULT_CONFIG['logging']

config['logging'].update(loggingdict)

print(config)

CONFIG_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "mqttms": {
            "type": "object",
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
        },
        "logging": {
            "type": "object",
            "properties": {
                "verbose": { "type": "boolean" }
            },
            "required": ["verbose"],
            "additionalProperties": False
        }
    },
    "required": ["mqttms", "logging"],
    "additionalProperties": False
}

try:
    validate(instance=config, schema=CONFIG_SCHEMA)
    print(f"Validates successfuly")
except ValidationError as e:
    print(f"Configuration validation error: {e}")