#!/usr/bin/python3
"""
qrz

"""

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


def shutdown(forced=False):
    '''bye bye'''
    if forced is True:
        os._exit(1)
    else:
        sys.exit()


def displayQRZImage(call):
    '''display qrz Image'''
    #r = requests.get('https://www.qrz.com/db/'+ call.lower())
    #soup = BeautifulSoup(r.content, "html")

    #image = soup.find("meta",  property="og:image")


def qrzRedisLookup(call):
    '''redis lookup'''
    try:
        data = redis.get('qrz' + call)
        if data is None:
            return False
        return json.loads(data)
    except KeyError:
        return False


def dictLookupAndPrint(lookup, color, what, newline=True, endchar=" "):
    '''lookup and print'''
    if what in lookup:
        if newline:
            print(fg(color) + str(lookup[what]))
        else:
            print(fg(color) + str(lookup[what]) + endchar, end='')
        return lookup[what]
    return None


def qrzLookup(origcall, config):
    '''Lookup call @QRZ'''
    my_lookuplib = LookupLib(lookuptype="qrz",
                             username=config['qrz.com']['username'],
                             pwd=config['qrz.com']['password'])
    cic = Callinfo(my_lookuplib)
    origcall = origcall.upper()
    try:
        call = cic.get_homecall(origcall)
        lookup = qrzRedisLookup(call)
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

    dictLookupAndPrint(lookup, '#a4a24f', 'fname', False)
    dictLookupAndPrint(lookup, '#a4a24f', 'name', False, ", ")

    dictLookupAndPrint(lookup, 'navajo_white_3', 'addr1', False, ", ")
    dictLookupAndPrint(lookup, 'navajo_white_3', 'zipcode', False)
    dictLookupAndPrint(lookup, 'navajo_white_3', 'addr2', False, ", ")
    dictLookupAndPrint(lookup, 'navajo_white_3', 'country')

    print(fg('#884444') + attr('bold') + 'Maidenhead: ', end="")
    dictLookupAndPrint(lookup, 'dark_sea_green_3b', 'locator', False)
    print(fg('#884444') + attr('bold') + 'Latitude: ', end="")
    dictLookupAndPrint(lookup, 'dark_sea_green_3b', 'latitude', False)
    print(fg('#884444') + attr('bold') + 'Longitude: ', end="")
    dictLookupAndPrint(lookup, 'dark_sea_green_3b', 'longitude')

    print(fg('#884444') + attr('bold') + 'CCode: ', end="")
    dictLookupAndPrint(lookup, 'dark_sea_green_3b', 'ccode', False)
    print(fg('#884444') + attr('bold') + 'CQZone: ', end="")
    dictLookupAndPrint(lookup, 'dark_sea_green_3b', 'cqz', False)
    print(fg('#884444') + attr('bold') + 'ITUZone: ', end="")
    dictLookupAndPrint(lookup, 'dark_sea_green_3b', 'ituz')

    print(fg('#884444') + attr('bold') + 'QSL: ', end="")
    dictLookupAndPrint(lookup, 'navajo_white_3', 'qslmgr', False)
    print(fg('#884444') + attr('bold') + 'eQSL: ', end="")
    dictLookupAndPrint(lookup, 'navajo_white_3', 'eqsl', False)
    print(fg('#884444') + attr('bold') + 'lotw: ', end="")
    dictLookupAndPrint(lookup, 'navajo_white_3', 'lotw')

    print(fg('#884444') + attr('bold') + 'E-Mail: ', end="")
    email = dictLookupAndPrint(lookup, 'navajo_white_3', 'email', False)
    print(attr('reset'))

    return {'origcallsign': origcall, 'callsign': callsign, 'email': email}


def ignore(config, data):
    '''restart'''
    if config['verbose'] is True:
        print('ignoring selection ' + data['origcallsign'] + ' ... reset')


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


def sendemail(config, data):
    '''email'''
    os.system(config['email']['exec'] + data['email'])


def appshutdown(config, data):
    '''bye bye'''
    if config['verbose'] is True:
        print("ignoring selection " + data['origcallsign'] +
              " shutdown requested...exiting")
    shutdown()


# Menu Options
menu_options = [
    "[o] (qso) starts qso", "[l] (qsl) ends qso]", "[r] rotate", "[e] email",
    "[i] ignore", "[x] exit"
]
options = {
    0: qso,
    1: qsl,
    2: rotate,
    3: sendemail,
    4: ignore,
    5: appshutdown,
}


def main():
    '''Main stuff'''

    historyfile = configdir + "/qrz-history"

    session = PromptSession(history=FileHistory(historyfile))

    while True:
        infinite = True
        try:
            callLookup = sys.argv[1]
            infinite = False
        except IndexError:
            try:
                call_completer = FuzzyWordCompleter(calls)

                message = [('class:message', 'enter call'),
                           ('class:prompt', '> ')]
                callLookup = session.prompt(
                    message,
                    style=style,
                    completer=call_completer,
                    enable_history_search=True,
                    auto_suggest=AutoSuggestFromHistory())
            except KeyboardInterrupt:
                shutdown(True)
        finally:
            if callLookup.lower() in ['exit', 'quit']:
                shutdown()
            else:
                data = qrzLookup(callLookup, cfg)
                if data['callsign'] is not None:
                    print(attr('reset'))
                    terminal_menu = TerminalMenu(menu_options,
                                                 title=data['callsign'] +
                                                 " (" + data['origcallsign'] +
                                                 ")")
                    menu_entry_index = terminal_menu.show()
                    try:
                        options[menu_entry_index](cfg, data)
                    except KeyError:
                        pass
            if not infinite:
                sys.exit()


if __name__ == "__main__":
    main()
