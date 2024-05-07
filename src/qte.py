#!/usr/bin/env python3
import os
import sys

import maidenhead as mh
import yaml
from colored import attr, fg
from geopy.geocoders import Nominatim
from prompt_toolkit.styles import Style
from pyhamtools.locator import (
    calculate_heading,
    calculate_heading_longpath,
    latlong_to_locator,
)


def calculate_bearing(d):
    dirs = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]
    ix = int(round(d / (360.0 / len(dirs))))
    return dirs[ix % len(dirs)]


style = Style.from_dict(
    {
        # User input (default text).
        "": "#ff0066",
        # Prompt.
        "message": "#884444",
        "prompt": "fg:#aa0022 bold",
    }
)

configdir = os.path.expanduser("~/.config/ham-tools")

with open(configdir + "/config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

address = " ".join(sys.argv[1:])
geolocator = Nominatim(user_agent="ON3URE_hamtools")
try:
    location = geolocator.geocode(address)

    locator1 = latlong_to_locator(cfg["qth"]["latitude"], cfg["qth"]["longitude"])
    locator2 = latlong_to_locator(location.latitude, location.longitude)

    heading = calculate_heading(locator1, locator2)
    longpath = calculate_heading_longpath(locator1, locator2)
    maidenhead = mh.to_maiden(location.latitude, location.longitude)

    print(
        fg("blue")
        + "-="
        + fg("turquoise_4")
        + attr("bold")
        + "QTE: Bearing lookup"
        + attr("reset")
        + fg("blue")
        + "=-"
        + attr("reset")
    )
    print(fg("light_magenta") + attr("bold") + "Address: ", end="")
    print(fg("dark_sea_green_3b") + location.address)
    print(fg("light_magenta") + attr("bold") + "Latitude: ", end="")
    print(fg("dark_sea_green_3b") + "%.1f°" % location.latitude, end="")
    print(fg("light_magenta") + attr("bold") + " Longitude: ", end="")
    print(fg("dark_sea_green_3b") + "%.1f°" % location.longitude, end="")
    print(fg("light_magenta") + attr("bold") + " Grid square: ", end="")
    print(fg("dark_sea_green_3b") + maidenhead)
    print()
    print(fg("light_magenta") + attr("bold") + "Heading: ", end="")
    print(fg("navajo_white_3") + "%.1f°" % heading, end="")
    print(fg("light_magenta") + attr("bold") + " Longpath: ", end="")
    print(fg("navajo_white_3") + "%.1f°" % longpath, end="")
    print(fg("light_magenta") + attr("bold") + " Bearing: ", end="")
    print(fg("navajo_white_3") + calculate_bearing(heading), end="")
except AttributeError:
    print("qte <address>")

print()
