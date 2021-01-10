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
from simple_term_menu import TerminalMenu
from pyhamtools import LookupLib, Callinfo
from colored import fg, attr
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import FuzzyWordCompleter
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


async def shutdown(forced=False):
    '''bye bye'''
    if forced is True:
        os._exit(1)
    else:
        sys.exit()


def displayQRZImage(call):
    '''display qrz Image'''
    mycall = call
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

    print(fg('#884444') + attr('bold') + 'Address: ', end="")

    await dictLookupAndPrint(lookup, '#a4a24f', 'fname', False)
    await dictLookupAndPrint(lookup, '#a4a24f', 'name', False, ", ")

    await dictLookupAndPrint(lookup, 'navajo_white_3', 'addr1', False, ", ")
    await dictLookupAndPrint(lookup, 'navajo_white_3', 'zipcode', False)
    await dictLookupAndPrint(lookup, 'navajo_white_3', 'addr2', False, ", ")
    await dictLookupAndPrint(lookup, 'navajo_white_3', 'country')

    print(fg('#884444') + attr('bold') + 'Maidenhead: ', end="")
    await dictLookupAndPrint(lookup, 'dark_sea_green_3b', 'locator', False)
    print(fg('#884444') + attr('bold') + 'Latitude: ', end="")
    await dictLookupAndPrint(lookup, 'dark_sea_green_3b', 'latitude', False)
    print(fg('#884444') + attr('bold') + 'Longitude: ', end="")
    await dictLookupAndPrint(lookup, 'dark_sea_green_3b', 'longitude')

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
    email =await  dictLookupAndPrint(lookup, 'navajo_white_3', 'email', False)
    print(attr('reset'))

    return {'origcallsign': origcall, 'callsign': callsign, 'email': email}


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

def googlemaps(config, data):
    '''googlemaps'''
    os.system(config['gmaps']['exec'] + data['latitude'] + " " + data['longitude'])

def sendemail(config, data):
    '''email'''
    os.system(config['email']['exec'] + data['email'])


async def appshutdown(config, data):
    '''bye bye'''
    if config['verbose'] is True:
        print("ignoring selection " + data['origcallsign'] +
              " shutdown requested...exiting")
    await shutdown()



# Menu Options
menu_options = [
    "[o] (qso) starts qso", "[l] (qsl) ends qso", "[r] rotate", "[e] email",
    "[g] google maps", "[i] ignore", "[x] exit"
]
options = {
    0: qso,
    1: qsl,
    2: rotate,
    3: sendemail,
    4: googlemaps,
    5: ignore,
    6: appshutdown,
}

session = PromptSession()

async def qrzLookupQueue():
    '''test'''
    global session
    while True:
        try:
            call = redis.lpop('qrzLookupQueue')
            if call is not None:
                #TODO cleanup call
                print()
                data = await qrzLookup(call, cfg)
                #TODO check call for action/ignore
                if data['callsign'] is not None:
                    terminal_menu = TerminalMenu(menu_options,
                                                 title=data['callsign'] +
                                                 " (" + data['origcallsign'] +
                                                 ")")
                    menu_entry_index = terminal_menu.show()
                    try:
                        await options[menu_entry_index](cfg, data)
                    except KeyError:
                        pass
                session.app.renderer.clear()
            else:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("Background task cancelled.")
            await shutdown()
        except NoneType:
            pass


async def main():
    '''Main stuff'''
    try:
        historyfile = configdir + "/qrz-history"

        global session
        session = PromptSession(history=FileHistory(historyfile),refresh_interval=1)
        
        background_task_qrz_lookup_queue = asyncio.create_task(qrzLookupQueue())

        while True:
            infinite = True
            if 1 in sys.argv:
                callLookup = sys.argv[1]
                infinite = False
            else:
                try:
                    call_completer = FuzzyWordCompleter(calls)

                    message = [('class:message', 'enter call'),
                               ('class:prompt', '> ')]
                    callLookup = await session.prompt_async(
                        message,
                        style=style,
                        completer=call_completer,
                        enable_history_search=True,
                        auto_suggest=AutoSuggestFromHistory())
                except KeyboardInterrupt:
                    await shutdown(True)
                if callLookup.lower() in ['exit', 'quit']:
                    await shutdown()
                elif callLookup is "":
                    pass
                else:
                    data = await qrzLookup(callLookup, cfg)
                    if data['callsign'] is not None:
                        await qsoLookup(data['callsign'])
                        if not infinite:
                            sys.exit()
                        print(attr('reset'))
                        terminal_menu = TerminalMenu(menu_options,
                                                     title=data['callsign'] +
                                                     " (" + data['origcallsign'] +
                                                     ")")
                        menu_entry_index = terminal_menu.show()
                        try:
                            await options[menu_entry_index](cfg, data)
                        except KeyError:
                            pass
                        session.app.renderer.clear()
    except EOFError:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
