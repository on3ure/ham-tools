#!/usr/bin/python3
"""
qte

"""

import sys
import json
import os
import yaml
import maidenhead as mh

from geopy.geocoders import Nominatim
from pyhamtools import LookupLib, Callinfo
from pyhamtools.locator import calculate_heading, calculate_heading_longpath, latlong_to_locator
from colored import fg, attr
from prompt_toolkit.styles import Style

style = Style.from_dict({
    # User input (default text).
    '': '#ff0066',

    # Prompt.
    'message': '#884444',
    'prompt': 'fg:#aa0022 bold'
})

configdir = os.path.expanduser('~/.config/ham-tools')

with open(configdir + '/config.yaml') as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

address=' '.join(sys.argv[1:])
geolocator = Nominatim(user_agent="ON3URE_hamtools")
try:
    location = geolocator.geocode(address)
        
    locator1 = latlong_to_locator(cfg['qth']['latitude'], cfg['qth']['longitude'])
    locator2 = latlong_to_locator(location.latitude, location.longitude)

    heading = calculate_heading(locator1, locator2)
    longpath = calculate_heading_longpath(locator1, locator2)
    maidenhead = mh.to_maiden(location.latitude, location.longitude)
            
    print(fg('blue') + '-=' + fg('turquoise_4') + attr('bold') + "QTE: Bearing lookup" + attr('reset') +
          fg('blue') + '=-' + attr('reset'))
    print(fg('#884444') + attr('bold') + 'Address: ', end="")
    print(fg('dark_sea_green_3b') + location.address)
    print(fg('#884444') + attr('bold') + 'Latitude: ', end="")
    print(fg('dark_sea_green_3b') + "%.1f°" % location.latitude, end="")
    print(fg('#884444') + attr('bold') + ' Longitude: ', end="")
    print(fg('dark_sea_green_3b') + "%.1f°" % location.longitude, end="")
    print(fg('#884444') + attr('bold') + ' Grid square: ', end="")
    print(fg('dark_sea_green_3b') + maidenhead )
    print()
    print(fg('#884444') + attr('bold') + 'Heading: ', end="")
    print(fg('navajo_white_3') + "%.1f°" % heading, end="")
    print(fg('#884444') + attr('bold') + ' Longpath: ', end="")
    print(fg('navajo_white_3') + "%.1f°" % longpath, end="")
except AttributeError:
    print("qte <address>")
