# ms_host.py

import time
import json
import struct
from cliapp.logger_module import logger, string_handler
from cliapp.mqtt_handler import MQTTHandler
from cliapp.ms_protocol import CommandProtocol

class MShost:
    def __init__(self, ms_protocol: CommandProtocol, config):
        self.ms_protocol = ms_protocol
        self.config = config

    def ms_who_am_i(self):
        payload = f'{{"command":"WH","data":""}}'
        self.ms_protocol.put_command(payload)

        self.ms_protocol.response_received.wait()
        payload = self.ms_protocol.response
        logger.info(f"MSH response: {payload}")
        self.ms_protocol.response_received.clear()
        return payload

    def ms_nop(self):
        pass

    def ms_sensors(self):
        payload = f'{{"command":"SR","data":""}}'
        self.ms_protocol.put_command(payload)

        self.ms_protocol.response_received.wait()
        payload = self.ms_protocol.response
        logger.info(f"MSH response: {payload}")
        self.ms_protocol.response_received.clear()
        return payload

    def ms_wificred():
        pass

    def ms_set_mode():
        pass

    def ms_getsmac():
        pass

    def ms_set_amb_thr():
        pass

    def ms_set_hum_thr():
        pass

    def ms_set_gas_thr():
        pass

    def ms_set_forced_time():
        pass

    def ms_set_post_time():
        pass

    def ms_ambient_light():
        pass

    def ms_get_params():
        pass

    def ms_start_vent():
        pass

    def ms_logs():
        pass

    def ms_mqtt_ready():
        pass