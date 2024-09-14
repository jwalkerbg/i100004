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
        pass

    def ms_nop(self):
        pass

    def ms_sensors(self):
        topic = self.ms_protocol.construct_cmd_topic()
        logger.info(f"CORE: {topic}")
        payl = f'{{"cid":{self.ms_protocol.generate_random_id_string()},"client":"{self.config["ms"].get("client_mac","_")}","command":"SR","data":""}}'
        self.ms_protocol.put_command(topic,payl)
        self.ms_protocol.response_received.wait()
        logger.info(f"CORE: {self.ms_protocol.response}")
        topic, payload = self.ms_protocol.response

        logger.info(f"MSH payload: {payload}")
        jp = json.loads(payload)
        jdata = jp.get('data', {})
        format_string = '<hIIIHBBB'
        bdata = bytes.fromhex(jdata)
        unpacked_data = struct.unpack(format_string, bdata)
        logger.info(f"MSH unpacked_data = {unpacked_data}")

        self.ms_protocol.response_received.clear()

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