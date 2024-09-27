import re

def match_mqtt_topic(mac_address: str, topic: str) -> bool:
    """
    Matches an MQTT topic with the following format:
    @/<mac_address>/RSP/<format>

    where mac_address is a 12-digit hexadecimal string and format is one of:
    'ASCII', 'ASCIIHEX', 'JSON', 'BINARY'.

    Args:
        mac_address (str): A 12-character hexadecimal MAC address.
        topic (str): The MQTT topic to validate.

    Returns:
        bool: True if the topic matches the expected format, False otherwise.
    """
    # Define the regex pattern for the MQTT topic, with valid formats embedded
    pattern = fr"^@/{mac_address}/RSP/(ASCII|ASCIIHEX|JSON|BINARY)$"

    # Check if the given topic matches the regex pattern
    return bool(re.match(pattern, topic))


def is_valid_mac_address(mac_address: str) -> bool:
    """
    Validates if the MAC address is correctly formatted.

    Args:
        mac_address (str): A 12-character hexadecimal MAC address.

    Returns:
        bool: True if mac_address is valid, False otherwise.
    """
    # Regex for the 12-digit hexadecimal MAC address
    mac_address_pattern = r"^[0-9A-Fa-f]{12}$"

    # Check if mac_address matches the pattern
    return bool(re.match(mac_address_pattern, mac_address))


# Test example
mac_address = "1234567890AB"
topic = "@/1234567890AB/RSP/JSOAN"

# First, validate mac_address
if is_valid_mac_address(mac_address):
    # If mac_address is valid, check if the topic matches the expected format
    result = match_mqtt_topic(mac_address, topic)
    print(f"Does the topic match? {result}")
else:
    print("Invalid MAC address.")
