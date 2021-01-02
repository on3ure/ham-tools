#!/usr/bin/python3
"""
qrz

"""

import sys
import json
import os
import yaml
from simple_term_menu import TerminalMenu
from pyhamtools import LookupLib, Callinfo
from colored import fg, attr
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
import redis

style = Style.from_dict({
    # User input (default text).
    '': '#ff0066',

    # Prompt.
    'message': '#884444',
    'prompt': 'fg:#aa0022 bold'
})
'''Redis'''
redis = redis.Redis(host='localhost',
                    port=6380,
                    db=0,
                    charset="utf-8",
                    decode_responses=True)
'''Preload Calls'''
calls = list(redis.smembers('qrzCALLS'))
'''Config dir'''
configdir = os.path.expanduser('~/.config/ham-tools')


def shutdown(forced=False):
    '''bye bye'''
    if forced is True:
        os._exit(1)
    else:
        sys.exit()


def qrzRedisLookup(call):
    '''redis lookup'''
    try:
        data = redis.get('qrz' + call)
        if data is None:
            return False
        return json.loads(data)
    except KeyError:
        return False


def qrzLookup(origcall, config):
    '''Lookup call @QRZ'''
    my_lookuplib = LookupLib(lookuptype="qrz",
                             username=config['qrz.com']['username'],
                             pwd=config['qrz.com']['password'])
    cic = Callinfo(my_lookuplib)
    origcall = origcall.upper()
    call = cic.get_homecall(origcall)
    lookup = qrzRedisLookup(call)
    #if lookup is False:
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
            return origcall, callsign
        except KeyError:
            callsign = call
            lookup = dict()
            print("Not Found")
            return origcall, callsign
    else:
        callsign = lookup['callsign']
    try:
        #print(lookup)
        print(fg('#f9b9b3') + callsign + ' (' + ','.join(lookup['aliases']) +
              ')')
    except TypeError:
        print(fg('#f9b9b3') + callsign)
    except KeyError:
        print(fg('#f9b9b3') + callsign)
    try:
        print(fg('#a4a24f') + lookup['fname'] + ' ' + lookup['name'])
    except KeyError:
        print("Anonymous")
    try:
        print(fg('navajo_white_3') + lookup['addr1'])
    except KeyError:
        pass
    try:
        print(fg('navajo_white_3') + lookup['addr2'])
    except KeyError:
        pass
    try:
        print(fg('navajo_white_3') + lookup['country'])
    except KeyError:
        pass
    try:
        print(fg('dark_sea_green_3b') + lookup['locator'])
    except KeyError:
        pass

    try:
        email = lookup['email']
    except KeyError:
        email = None

    data = {'origcallsign': origcall, 'callsign': callsign, 'email': email}

    return data


def ignore(config, data):
    '''restart'''
    if config['verbose'] is True:
        print('ignoring selection ' + data['origcallsign'] + ' ... reset')


def qso(config, data):
    '''log qso'''
    os.system(config['qso']['exec'] + data['origcallsign'] + '" "' + data['callsign'] + '"')


def qsl(config, data):
    '''qsl'''
    os.system(config['qsl']['exec'] + data['origcallsign'] + '" "' + data['callsign'] + '"')


def rotate(config, data):
    '''rotate'''
    os.system(config['rotate']['exec'] + data['origcallsign'] + '" "' + data['callsign'] + '"')


def sendemail(config, data):
    '''email'''
    os.system(config['email']['exec'] + data['email'])


def appshutdown(config, data):
    '''bye bye'''
    if config['verbose'] is True:
        print("ignoring selection " + data['origcallsign'] + " shutdown requested...exiting")
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

    with open(configdir + '/config.yaml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

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
                data = qrzLookup(callLookup, config)
                if data['callsign'] is not None:
                    print(attr('reset'))
                    terminal_menu = TerminalMenu(menu_options,
                                                 title=data['callsign'] +
                                                 " (" + data['origcallsign'] +
                                                 ")")
                    menu_entry_index = terminal_menu.show()
                    options[menu_entry_index](config, data)
            if not infinite:
                sys.exit()


if __name__ == "__main__":
    main()
