#!/usr/bin/env python
# *-* encoding: utf8
# 
# Copyright (c) 2006 Stian Soiland
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Author: Stian Soiland <stian@soiland.no>
# URL: http://soiland.no/i/src/
# License: MIT
#
"""UUID generator.

Generate Universally Unique IDentifiers (UUID) as defined by
RFC 4122. An UUID is 128 bit long and is guaranteed unique across time
and space.

Currently this module can generating UUIDs by UUID version 4, the
random generation. The official versions are:

v1 Host and time-based 
v2 DCE Security, with POSIX UIDs
v3 Name-based with MD5 hashing
v4 Random or pseudo-random
v5 Name-based with SHA-1 hashing
"""


import random

# Random UUID generator as in RFC4122
# ftp://ftp.rfc-editor.org/in-notes/rfc4122.txt

# octet     6 7 8 9 a b c d e f 
_V4_NOT = 0xf000c000000000000000
_V4_OR =  0x40008000000000000000
# bit6=0 and bit7=1 in octet 8  --> variant DCE 1.1, ISO/IEC 11578:1996
# bit 4..7 of octet 6 is the version number, here v4

def random_uuid():
    """Generate a random (v4) uuid. Return as long."""
    return random.getrandbits(128) & ~_V4_NOT | _V4_OR


def uuid_str(uuid=None):
    """Format a UUID integer as a string. 
    If uuid is not given, a new, random uuid is generated.
    """
    if uuid is None:
        uuid = random_uuid()
    # We'll split it up as in the RFC for clarity
    node = uuid & ((1<<48)-1)
    uuid >>= 48
    
    clock_seq_low = uuid & 0xff
    uuid >>= 8

    clock_seq_hi = uuid & 0xff
    uuid >>= 8
    
    time_hi = uuid & 0xffff
    uuid >>= 16
    
    time_mid = uuid & 0xffff    
    uuid >>= 16

    time_low = uuid & 0xffffffff
    uuid >>= 32

    assert uuid == 0, "uuid larger than 128 bit"

    return "%08x-%04x-%04x-%02x%02x-%012x" % (
            time_low, time_mid, time_hi, 
            clock_seq_hi, clock_seq_low, node)


def parse(uuid):
    """Parse uuid string, return as long"""
    #dc1804b0-07c7-11db-8858-a38955089441
    return long(uuid.replace("-", ""), 16)


if __name__ == "__main__":
    assert (uuid_str(0x123456789abcdefedcba987654321012) == 
                "12345678-9abc-defe-dcba-987654321012")

    assert (parse("12345678-9abc-defe-dcba-987654321012") ==
                  0x123456789abcdefedcba987654321012)
    uuid_s = uuid_str() 
    uuid = parse(uuid_s)
    assert 0 < uuid < 1<<128
    assert uuid_str(uuid) == uuid_s
    print uuid_str()
# Tip: Try uuid -d $(python uuid.py)   using OSSP uuid
