# mqtt_dispatcher.py

from typing import Dict, Tuple, Any
from abc import ABC, abstractmethod
from mqttms.logger_module import logger

class AbstractMQTTDispatcher(ABC):
    def __init__(self, config: Dict):
        self.config = config
        logger.info(f"AbstractMQTTDispatcher __init__")

    @abstractmethod
    def handle_message(self, message: Tuple[str, str]) -> bool:
        return False
