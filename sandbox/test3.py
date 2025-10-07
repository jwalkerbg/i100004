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


def is_valid_uuid(uuid: str) -> bool:
    """
    Validates if the UUID is correctly formatted.

    Args:
        uuid (str): A 12-character hexadecimal UUID.

    Returns:
        bool: True if uuid is valid, False otherwise.
    """
    # Regex for the 12-digit hexadecimal UUID
    uuid_pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"

    # Check if uuid matches the pattern
    return bool(re.match(uuid_pattern, uuid))


# Test example
uuid = "1234567890AB"
topic = "@/1234567890AB/RSP/JSON"

# First, validate uuid
if is_valid_uuid(uuid):
    # If uuid is valid, check if the topic matches the expected format
    result = match_mqtt_topic(uuid, topic)
    print(f"Does the topic match? {result}")
else:
    print("Invalid UUID.")
