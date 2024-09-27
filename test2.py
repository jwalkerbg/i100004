import struct

# Example hexadecimal string (21 bytes, or 42 hex characters)
hex_string = "0a0b1a2b3c4d5e6f7a8b9c0d0e1f2f3f4f5f12"

# Convert the hexadecimal string to bytes (21 bytes expected)
data = bytes.fromhex(hex_string)

# Define the format string with explicit padding
format_string = '<hIIIHBBB'

# Unpack the data using the new format string
unpacked_data = struct.unpack(format_string, data)

# Print unpacked data to see how it fills the struct fields
print("Unpacked data:", unpacked_data)

# Example values for packing (replace with real values as needed)
values = (-2587, 11259375, 12345678, 87654321, 2048, 1, 0, 1)

# Pack the values into a byte sequence, with explicit padding byte
packed_data = struct.pack(format_string, *values)

# Convert packed data back to a hex string (for verification)
hex_representation = packed_data.hex()
print("Packed hex string:", hex_representation)

format_string = "B"
value = 76
#packed_data = struct.pack(format_string, value)
hex_representation = struct.pack(format_string, value).hex()
print(hex_representation)

def create_byte_array(ssid: str, password: str) -> bytearray:
    # Convert the ssid and password strings to ASCII bytes
    ssid_bytes = ssid.encode('ascii')
    password_bytes = password.encode('ascii')

    # Create a bytearray that includes both ssid and password, separated by a null byte (\0)
    result = bytearray(ssid_bytes) + b'\0' + bytearray(password_bytes)

    return result

ssid = "iv_cenov"
password = "6677890vla"

ba = create_byte_array(ssid, password)
hba = ba.hex()
print(ba)
print(hba)


adict = {}
adict[1] = "1"

bdict = {}

if adict:
    print(f"adict is not empty")
else:
    print(f"adict is empty")

if bdict:
    print(f"bdict is not empty")
else:
    print(f"bdict is empty")
