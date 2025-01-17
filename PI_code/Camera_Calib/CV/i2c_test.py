#!/bin/python3

from smbus2 import SMBus
import struct

i2c = SMBus()
i2c.open(1)

# Move 1 meter, turn 90 degrees

# Write Arduino address, dummy byte (smbus2 doesn't expose low-level write commands), 
# float representation of dist, float representation of phi, and CTRL reg as a single list
i2c.write_i2c_block_data(8, 0, [i for i in struct.pack('f', 1)] + [i for i in struct.pack('f', 1.57)] + [0b1000_0000])

# Could also probably be implemented like this, just haven't tested yet
"""
cmd = [i for i in struct.pack('f', 1)] + [i for i in struct.pack('f', 1.57)] + [0b1000_0000]
i2c.write_i2c_block_data(8, 0, cmd)
"""
