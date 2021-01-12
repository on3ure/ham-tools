#!/usr/bin/python3
"""
qrz

"""

import asyncio
import sys
import json
import os
import yaml
import requests
import dumper

from pyhamtools import LookupLib, Callinfo
from colored import fg, attr
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from bs4 import BeautifulSoup
import redis

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

redis = redis.Redis(host='localhost',
                    port=cfg['redis']['port'],
                    db=0,
                    charset="utf-8",
                    decode_responses=True)

calls = list(redis.smembers('qrzCALLS'))
commands = {
    'lookup': {},
    'qso': None,
    'exit': None,
    'quit': None,
    'rotate': None,
    'email': None,
    'maps': None
}

for item in calls:
    commands['lookup'][str(item)] = None

historyfile = configdir + "/qrz-history"
session = PromptSession(history=FileHistory(historyfile))


async def shutdown():
    '''bye bye'''
    os._exit(1)


def displayQRZImage(call):
    '''display qrz Image'''
    mycall = call
    print(mycall)
    #r = requests.get('https://www.qrz.com/db/'+ call.lower())
    #soup = BeautifulSoup(r.content, "html")

    #image = soup.find("meta",  property="og:image")


async def qrzRedisLookup(call):
    '''redis lookup'''
    try:
        data = redis.get('qrz' + call)
        if data is None:
            return False
        return json.loads(data)
    except KeyError:
        return False


async def dictLookupAndPrint(lookup, color, what, newline=True, endchar=" "):
    '''lookup and print'''
    if what in lookup:
        if newline:
            print(fg(color) + str(lookup[what]))
        else:
            print(fg(color) + str(lookup[what]) + endchar, end='')
        return lookup[what]
    return None


async def qsoRedisLookup(call):
    '''Lookup last QSO'''
    try:
        data = redis.get('qrzLASTCALL' + call)
        if data is None:
            return False
        return json.loads(data)
    except KeyError:
        return False


async def qsoLookup(call):
    '''Lookup last QSO'''
    data = await qsoRedisLookup(call)
    if data:
        print()
        print(fg('blue') + '-=' + fg('#FF0000') + attr('bold') + "Last QSO" + attr('reset') +
              fg('blue') + '=-' + attr('reset'))
        print(fg('#884444') + attr('bold') + 'Operator: ', end="")
        print(fg('dark_sea_green_3b') + data['operator'], end=" ")
        print(fg('#884444') + attr('bold') + 'Station: ', end="")
        print(fg('dark_sea_green_3b') + data['station'])
        print(fg('#884444') + attr('bold') + 'Date: ', end="")
        print(fg('dark_sea_green_3b') + data['date'], end=" ")
        print(fg('#884444') + attr('bold') + 'Band: ', end="")
        print(fg('dark_sea_green_3b') + data['band'], end=" ")
        print(fg('#884444') + attr('bold') + 'Mode: ', end="")
        print(fg('dark_sea_green_3b') + data['mode'], end=" ")
        print(fg('#884444') + attr('bold') + 'QSL Send: ', end="")
        print(fg('dark_sea_green_3b') + data['qsl_send'], end=" ")
        print(fg('#884444') + attr('bold') + 'QSL Received: ', end="")
        print(fg('dark_sea_green_3b') + data['qsl_rcvd'])


async def qrzLookup(origcall, config):
    '''Lookup call @QRZ'''
    my_lookuplib = LookupLib(lookuptype="qrz",
                             username=config['qrz.com']['username'],
                             pwd=config['qrz.com']['password'])
    cic = Callinfo(my_lookuplib)
    origcall = origcall.upper()
    try:
        call = cic.get_homecall(origcall)
        lookup = await qrzRedisLookup(call)
    except ValueError:
        callsign = None
        lookup = dict()
        print("Not Found")
        return {'origcallsign': origcall, 'callsign': callsign}
    if lookup is False:
        try:
            lookup = cic.get_all(call)
            callsign = lookup['callsign']
            redis.set('qrz' + call.upper(), json.dumps(lookup, default=str))
            redis.expire('qrz' + call.upper(), 2629743000)
            redis.sadd('qrzCALLS', call.upper())
            calls.append(call.upper())
        except ValueError:
            callsign = None
            lookup = dict()
            print("Not Found")
            return {'origcallsign': origcall, 'callsign': callsign}
        except KeyError:
            callsign = call
            lookup = dict()
            print("Not Found")
            return {'origcallsign': origcall, 'callsign': callsign}
    else:
        callsign = lookup['callsign']

    if callsign and 'aliases' in lookup:
        print(fg('blue') + '-=' + fg('turquoise_4') + attr('bold') + callsign + attr('reset') +
              fg('blue') + '=-' + attr('reset') + " (" + ','.join(lookup['aliases']) +
              ')')
    else:
        print(fg('blue') + '-=' + fg('turquoise_4') + attr('bold') + callsign +
              fg('blue') + '=-')

    print(fg('#884444') + attr('bold') + 'QTH: ', end="")

    await dictLookupAndPrint(lookup, '#a4a24f', 'fname', False)
    await dictLookupAndPrint(lookup, '#a4a24f', 'name', False, ", ")

    await dictLookupAndPrint(lookup, 'navajo_white_3', 'addr1', False, ", ")
    await dictLookupAndPrint(lookup, 'navajo_white_3', 'zipcode', False)
    await dictLookupAndPrint(lookup, 'navajo_white_3', 'addr2', False, ", ")
    await dictLookupAndPrint(lookup, 'navajo_white_3', 'country')

    print(fg('#884444') + attr('bold') + 'Grid square: ', end="")
    await dictLookupAndPrint(lookup, 'dark_sea_green_3b', 'locator', False)
    print(fg('#884444') + attr('bold') + 'Latitude: ', end="")
    latitude = await dictLookupAndPrint(lookup, 'dark_sea_green_3b', 'latitude', False)
    print(fg('#884444') + attr('bold') + 'Longitude: ', end="")
    longitude = await dictLookupAndPrint(lookup, 'dark_sea_green_3b', 'longitude')

    print(fg('#884444') + attr('bold') + 'CCode: ', end="")
    await dictLookupAndPrint(lookup, 'dark_sea_green_3b', 'ccode', False)
    print(fg('#884444') + attr('bold') + 'CQZone: ', end="")
    await dictLookupAndPrint(lookup, 'dark_sea_green_3b', 'cqz', False)
    print(fg('#884444') + attr('bold') + 'ITUZone: ', end="")
    await dictLookupAndPrint(lookup, 'dark_sea_green_3b', 'ituz')

    print(fg('#884444') + attr('bold') + 'QSL: ', end="")
    await dictLookupAndPrint(lookup, 'navajo_white_3', 'qslmgr', False)
    print(fg('#884444') + attr('bold') + 'eQSL: ', end="")
    await dictLookupAndPrint(lookup, 'navajo_white_3', 'eqsl', False)
    print(fg('#884444') + attr('bold') + 'lotw: ', end="")
    await dictLookupAndPrint(lookup, 'navajo_white_3', 'lotw')

    print(fg('#884444') + attr('bold') + 'E-Mail: ', end="")
    email = await  dictLookupAndPrint(lookup, 'navajo_white_3', 'email', False)
    print(attr('reset'))

    return {'origcallsign': origcall, 'callsign': callsign, 'email': email, 'latitude': latitude, 'longitude': longitude}


async def ignore(config, data):
    '''restart'''
    if config['verbose'] is True:
        print('ignoring selection ' + data['origcallsign'] + ' ... reset')
    print()


def qso(config, data):
    '''log qso'''
    os.system(config['qso']['exec'] + data['origcallsign'] + '" "' +
              data['callsign'] + '"')


def qsl(config, data):
    '''qsl'''
    os.system(config['qsl']['exec'] + data['origcallsign'] + '" "' +
              data['callsign'] + '"')


def rotate(config, data):
    '''rotate'''
    os.system(config['rotate']['exec'] + data['origcallsign'] + '" "' +
              data['callsign'] + '"')


def maps(config, data):
    '''maps'''
    os.system(config['maps']['exec'] + " " +
              str(data['latitude']) + " " + str(data['longitude']))


def sendemail(config, data):
    '''email'''
    os.system(config['email']['exec'] + data['email'])


async def appshutdown(config, data):
    '''bye bye'''
    if config['verbose'] is True:
        print("ignoring selection " + data['origcallsign'] +
              " shutdown requested...exiting")
    await shutdown()


async def qrzLookupQueue():
    '''test'''
    while True:
        try:
            call = redis.lpop('qrzLookupQueue')
            if call is not None:
                session.default_buffer.text = "lookup " + call
                session.default_buffer.validate_and_handle()
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            await shutdown()


async def main():
    '''Main stuff'''
    try:
        asyncio.create_task(qrzLookupQueue())

        data = None

        while True:
            infinite = True
            if 1 in sys.argv:
                callLookup = "lookup " + sys.argv[1]
                infinite = False
            else:
                try:
                    call_completer = NestedCompleter.from_nested_dict(commands)

                    message = [('class:message', 'qrz'),
                               ('class:prompt', '> ')]
                    callLookup = await session.prompt_async(
                        message,
                        style=style,
                        completer=call_completer,
                        complete_while_typing=True,
                        enable_history_search=True,
                        auto_suggest=AutoSuggestFromHistory())
                except KeyboardInterrupt:
                    await shutdown()

                command = (callLookup.lower().split(sep=" ", maxsplit=2))[0]

                if command in ['exit', 'quit', 'rotate', 'email', 'maps']:
                    if command in ['']:
                        pass
                    if command in ['exit', 'quit']:
                        await shutdown()
                    if command in ['email']:
                        if data is None:
                            print("First do a lookup !")
                        else:
                            sendemail(cfg, data)
                    if command in ['rotate']:
                        if data is None:
                            print("First do a lookup !")
                        else:
                            rotate(cfg, data)
                    if command in ['maps']:
                        if data is None:
                            print("First do a lookup !")
                        else:
                            print("Start maps")
                            maps(cfg, data)

                if command in ['lookup']:
                    data = await qrzLookup(callLookup, cfg)
                    if data['callsign'] is not None:
                        await qsoLookup(data['callsign'])
                        print()
                        if not infinite:
                            sys.exit()
    except EOFError:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
