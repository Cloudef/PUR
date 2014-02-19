#!/usr/bin/env python3
# pylint: disable=line-too-long
"""freegeoip python3 module"""

import re, json
from urllib.request import urlopen

def valid_ip(ipa):
    """check that given ip is valid"""
    pattern = r"\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
    return re.match(pattern, ipa)

def get_geodata(ipa):
    """geocode IP"""
    if not valid_ip(ipa):
        raise ValueError('Invalid IP format', 'You must enter a valid ip format: X.X.X.X')
    url = 'http://freegeoip.net/json/{}'.format(ipa)
    data = urlopen(url).readall().decode('UTF-8')
    if not data:
        return None
    return json.loads(data)

#  vim: set ts=8 sw=4 tw=0 :
