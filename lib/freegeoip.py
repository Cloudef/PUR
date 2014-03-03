#!/usr/bin/env python3
# pylint: disable=line-too-long
"""freegeoip python3 module"""

import re, json
from urllib.request import urlopen
from urllib.error import URLError

def valid_ip(ipa):
    """check that given ip is valid"""
    pattern = r"\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
    return re.match(pattern, ipa)

def get_geodata(ipa):
    """geocode IP"""
    if not valid_ip(ipa):
        raise ValueError('Invalid IP format', 'You must enter a valid ip format: X.X.X.X')

    if ipa == '127.0.0.1':
        data = {'city': 'Localhost Town'}
        return data

    url = 'http://freegeoip.net/json/{}'.format(ipa)

    try:
        data = urlopen(url, timeout=5).readall().decode('UTF-8')
        if not data:
            return None
        return json.loads(data)
    except URLError:
        pass

    return None

#  vim: set ts=8 sw=4 tw=0 :
