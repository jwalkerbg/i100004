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

    def ms_simple_command(self, cmd: str):
        payload = f'{{"command":"{cmd}","data":""}}'
        self.ms_protocol.put_command(payload)

        self.ms_protocol.response_received.wait()
        payload = self.ms_protocol.response
        logger.info(f"MSH response: {payload}")
        self.ms_protocol.response_received.clear()
        return payload

    def ms_who_am_i(self):
        return self.ms_simple_command("WH")

    def ms_nop(self):
        return self.ms_simple_command("NP")

    def ms_sensors(self):
        payload = f'{{"command":"SR","data":""}}'
        self.ms_protocol.put_command(payload)

        self.ms_protocol.response_received.wait()
        payload = self.ms_protocol.response
        logger.info(f"MSH response: {payload}")
        self.ms_protocol.response_received.clear()
        return payload

    def ms_wificred(self):
        pass

    def ms_set_mode(self):
        pass

    def ms_getsmac(self):
        return self.ms_simple_command("GM")

    def ms_set_amb_thr(self):
        pass

    def ms_set_hum_thr(self):
        pass

    def ms_set_gas_thr(self):
        pass

    def ms_set_forced_time(self):
        pass

    def ms_set_post_time(self):
        pass

    def ms_ambient_light(self):
        pass

    def ms_get_params(self):
        return self.ms_simple_command("PG")

    def ms_start_vent(self):
        return self.ms_simple_command("SV")

    def ms_logs(self):
        pass

    def ms_mqtt_ready(self):
        return self.ms_simple_command("MQ")