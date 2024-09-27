import re

class A:
    def __init__(self):
        print("A's __init__ called")

class B(A):
    def __init__(self):
        super().__init__()  # Calls A's __init__
        print("B's __init__ called")

class C(A):
    def __init__(self):
        super().__init__()  # Calls A's __init__
        print("C's __init__ called")

class D(B, C):
    def __init__(self):
        super().__init__()  # Follows MRO to call B, then C
        print("D's __init__ called")

print("\n")
d = D()

string = '1234'
hrisovul = { }

def string_by_ref(sss):
    sss["st"] = {"epi":12, "data":"sdfdsfsf"}

print(f"{hrisovul}")
string_by_ref(hrisovul)
print(f"{hrisovul}")

tup = (11, 22)
print(f"tup[0] = {tup[0]}")
print(f"tup[1] = {tup[1]}")

def check_mqtt_topic_format(topic, valid_formats):
    # Split the topic by '/'
    topic_parts = topic.split('/')

    # Ensure the topic has at least 4 elements and the last element is the format
    if len(topic_parts) < 4:
        return -1

    # Extract the format (last element of the topic)
    format_part = topic_parts[-1]

    # Check if the format part is in the array of valid formats
    if format_part in valid_formats:
        return valid_formats.index(format_part)  # Return the index of the found format
    else:
        return -1  # Return -1 if not found

import json

def check_mqtt_topic_format(topic, valid_formats, mapped_formats):
    # Split the topic by '/'
    topic_parts = topic.split('/')

    # Ensure the topic has at least 4 elements and the last element is the format
    if len(topic_parts) < 4:
        return None

    # Extract the format (last element of the topic)
    format_part = topic_parts[-1]

    # Check if the format part is in the array of valid formats
    if format_part in valid_formats:
        # Find the index in valid_formats and map to mapped_formats
        index = valid_formats.index(format_part)
        mapped_value = mapped_formats[index]

        # Create the JSON object
        jsl = {"dataType": mapped_value}
        return jsl
    else:
        return None  # Return None if not found

# Valid formats array
valid_formats = ["BINARY", "ASCIIHEX", "ASCII", "JSON"]

# Mapped formats array (to match the valid formats by index)
mapped_formats = ["base64", "asciihex", "ascii", "object"]

# Test with a valid topic
topic1 = "@/mac/CMD/BINARY"
result1 = check_mqtt_topic_format(topic1, valid_formats, mapped_formats)
print(f"Result for '{topic1}': {json.dumps(result1, indent=2)}")
# Output: { "dataType": "base64" }

# Test with another valid topic
topic2 = "@/mac/CMD/JSON"
result2 = check_mqtt_topic_format(topic2, valid_formats, mapped_formats)
print(f"Result for '{topic2}': {json.dumps(result2, indent=2)}")
# Output: { "dataType": "object" }

# Test with another valid topic
topic3 = "@/mac/CMD/ASCIIHEX"
result3 = check_mqtt_topic_format(topic3, valid_formats, mapped_formats)
print(f"Result for '{topic3}': {json.dumps(result3, indent=2)}")
# Output: { "dataType": "object" }



# Test with an invalid format
topic3 = "@/mac/CMD/INVALIDFORMAT"
result3 = check_mqtt_topic_format(topic3, valid_formats, mapped_formats)
print(f"Result for '{topic3}': {result3}")
# Output: None

def insert_after_substring_regex(s1, s2, s3):
    # Use re.sub to find s3 and replace it with s3 followed by s1
    new_string = re.sub(f'({s3})', r'\1' + s1, s2)
    return new_string

# Example usage:
s11 = '"key1":1,'
s12 = '"key2":2,'
s2 = '{"key3":"value3","key4":"value4"}'
s3 = '({)'

result = insert_after_substring_regex(s12, s2, s3)
print(result)

result = insert_after_substring_regex(s11, result, s3)
print(result)