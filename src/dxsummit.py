#!/usr/bin/python3
'''DXSummit CLI by ON3URE'''

import asyncio
import hashlib
import os
import redis
import yaml
import requests
#import dumper

#from colored import fg, attr
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import (
    Checkbox,
    Frame,
    SelectList,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from bs4 import BeautifulSoup
#from cStringIO import StringIO

configdir = os.path.expanduser('~/.config/ham-tools')

with open(configdir + '/config.yaml') as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

redis = redis.Redis(host='localhost',
                    port=cfg['redis']['port'],
                    db=0,
                    charset="utf-8",
                    decode_responses=True)

globalvars = {
        "lastcall": None,
}
mode = set()
special = set()

auto_tune = Checkbox(text="auto tune")
qrz = Checkbox(text="lookup qrz")
current_band_only = Checkbox(text="follow band decoder")
phone = Checkbox(text="phone")
cw = Checkbox(text="cw")
digi = Checkbox(text="digi")

mobile = Checkbox(text="Mobile (/M)".rjust(10))
qrp = Checkbox(text="Qrp (/QRP)")
portable = Checkbox(text="Portable (/P)".rjust(10))
beacon = Checkbox(text="Beacon (/B)".rjust(10))
iota = Checkbox(text="iota")
sat = Checkbox(text="satelite")

radios = SelectList(
    values=[('a', ' ')]
)

frequency = Window(
    FormattedTextControl(HTML('<b fg="#884444">Freq.:</b> ' + "10000.0 Khz".rjust(15))),
    ignore_content_width=True,
    style="class:info",
    align=WindowAlign.CENTER,
)

dx = Window(
    FormattedTextControl(HTML('<b fg="#884444">Call:</b> ' + "NONE".rjust(12))),
    ignore_content_width=True,
    style="class:info",
    align=WindowAlign.RIGHT,
)

current_band = Window(
    FormattedTextControl(HTML('<b fg="#884444">Band:</b> 80M')),
    ignore_content_width=True,
    style="class:info",
    align=WindowAlign.LEFT,
)


title = "Spotter".ljust(15) + "Freq." . ljust(8) + "DX".ljust(13) + \
    "Info".ljust(35) + "Time".ljust(15) + "Country".ljust(500)

toggle_one = VSplit([auto_tune, qrz, current_band_only, phone, cw,  digi], padding=1)
toggle_two = VSplit([ mobile, portable, beacon, qrp, sat, iota], padding=1)

container = HSplit(
    [
        Frame(title=title, body=radios),
        Frame(
            title="toggle by first letter",
            body=HSplit([toggle_one,toggle_two],padding_char='-',padding=1)
        ),
        Frame(
            title="tuning info",
            body=VSplit([current_band,frequency,dx],padding=1, style='class:info')
        )
    ]
)

# Global key bindings.
bindings = KeyBindings()
bindings.add("tab")(focus_next)
bindings.add("s-tab")(focus_previous)


@bindings.add('c-c')
@bindings.add('q')
@bindings.add('escape')
def exit_(event):
    '''exit'''
    event.app.exit()

@bindings.add('a')
def auto_tune_(event):
    '''exit'''
    if auto_tune.checked is True:
        auto_tune.checked = False
    else:
        auto_tune.checked = True
        radios.current_value = radios.values[radios._selected_index][0]
        tunedata = radios.current_value.split(sep=" ", maxsplit=3)
        globalvars['lastcall'] = tunedata[2]
        if qrz.checked is True:
            redis.rpush('qrzLookupQueue', tunedata[2])
        frequency.content=FormattedTextControl(HTML('<b fg="#884444">Freq.:</b> ' + (tunedata[1] + " Khz").rjust(15)))
        dx.content=FormattedTextControl(HTML('<b fg="#884444">Call:</b> ' + tunedata[2].rjust(12)))
        event.app.invalidate()
    event.app.invalidate()
    #print(str(dir(auto_tune)).replace(",","\n"))

@bindings.add('l')
def qrz_(event):
    '''exit'''
    if qrz.checked is True:
        qrz.checked = False
    else:
        qrz.checked = True
    event.app.invalidate()

@bindings.add('p')
def phone_(event):
    '''toggle phone'''
    if phone.checked is True:
        phone.checked = False
        mode.remove('PHONE')
    else:
        phone.checked = True
        mode.add('PHONE')
    event.app.invalidate()


@bindings.add('c')
def cw_(event):
    '''toggle cw'''
    if cw.checked is True:
        cw.checked = False
        mode.remove('CW')
    else:
        cw.checked = True
        mode.add('CW')
    event.app.invalidate()


@bindings.add('d')
def digi_(event):
    '''toggle digi'''
    if digi.checked is True:
        digi.checked = False
        mode.remove('DIGI')
    else:
        digi.checked = True
        mode.add('DIGI')
    event.app.invalidate()


@bindings.add('f')
def follow_(event):
    '''toggle digi'''
    if current_band_only.checked is True:
        current_band_only.checked = False
    else:
        current_band_only.checked = True
    event.app.invalidate()

@bindings.add('M')
def mobile_(event):
    '''toggle mobile'''
    if mobile.checked is True:
        mobile.checked = False
    else:
        mobile.checked = True
        beacon.checked = False
        portable.checked = False
    event.app.invalidate()

@bindings.add('P')
def portable_(event):
    '''toggle portable'''
    if portable.checked is True:
        portable.checked = False
    else:
        portable.checked = True
        beacon.checked = False
        mobile.checked = False
    event.app.invalidate()

@bindings.add('B')
def beacon_(event):
    '''toggle beacon'''
    if beacon.checked is True:
        beacon.checked = False
    else:
        beacon.checked = True
        portable.checked = False
        mobile.checked = False
    event.app.invalidate()

@bindings.add('Q')
def qrp_(event):
    '''toggle qrp'''
    if qrp.checked is True:
        qrp.checked = False
    else:
        qrp.checked = True
    event.app.invalidate()

@bindings.add('s')
def satelite_(event):
    '''toggle satelite'''
    if sat.checked is True:
        sat.checked = False
    else:
        sat.checked = True
    event.app.invalidate()

@bindings.add('i')
def iota_(event):
    '''toggle iota'''
    if iota.checked is True:
        iota.checked = False
    else:
        iota.checked = True
    event.app.invalidate()

@bindings.add('tab', eager=True)
def _(event):
    ''' do nothing '''
    dx.text=str(mode)
    event.app.invalidate()

@bindings.add('enter', eager=True)
@bindings.add('t', eager=True)
@bindings.add(' ', eager=True)
def _(event):
    ''' update frequency/call '''
    radios.current_value = radios.values[radios._selected_index][0]
    tunedata = radios.current_value.split(sep=" ", maxsplit=3)
    globalvars['lastcall'] = tunedata[2]
    if qrz.checked is True:
        redis.rpush('qrzLookupQueue', tunedata[2])
    frequency.content=FormattedTextControl(HTML('<b fg="#884444">Freq.:</b> ' + (tunedata[1] + " Khz").rjust(15)))
    dx.content=FormattedTextControl(HTML('<b fg="#884444">Call:</b> ' + tunedata[2].rjust(12)))
    event.app.invalidate()

async def update_spots(application):
    """
    Coroutine that updates spots
    """
    lasthash = ""
    try:
        while True:
            r = requests.get(
                'http://www.dxsummit.fi/DxSpots.aspx?count=50&include_modes=PHONE')
            cleantext = BeautifulSoup(r.text, "lxml").get_text()
            currenthash = hashlib.md5(cleantext.encode('utf-8')).hexdigest()

            clusterdata = []

            i = 0
            for line in cleantext.splitlines():
                line = line[:73] + ':' + line[73:]
                #line = line[:76] + line[84:]
                cleanline = ' '.join(line.split())
                splitstring = cleanline.split(sep=" ", maxsplit=3)
                clusterdata.append(
                    (hashlib.md5(line.encode('utf-8')).hexdigest() + " " + splitstring[1]+" "+splitstring[2], " " + line))
                data = cleanline.split(sep=" ", maxsplit=3)
                if ((auto_tune.checked is True) and (i == 0) and (data[2] != globalvars['lastcall'])):
                    globalvars['lastcall'] = data[2]
                    frequency.content=FormattedTextControl(HTML('<b fg="#884444">Freq.:</b> ' + (data[1] + " Khz").rjust(15)))
                    dx.content=FormattedTextControl(HTML('<b fg="#884444">Call:</b> ' + data[2].rjust(12)))
                    if qrz.checked is True:
                        redis.rpush('qrzLookupQueue',data[2])
                i+=1

            radios.values = clusterdata

            if currenthash != lasthash:
                application.invalidate()
                await asyncio.sleep(15)
            else:
                await asyncio.sleep(30)
    except asyncio.CancelledError:
        #TODO safe config here ?
        print()

async def main():
    ''' Main stuff '''
    application = Application(
        layout=Layout(container),
        key_bindings=bindings,
        mouse_support=False,
        full_screen=True,
        style=Style.from_dict({
            #'dialog': 'bg:#cdbbb3',
            #'button': 'bg:#bf99a4',
            'checkbox': '#a4a24f',
            #'dialog.body': 'bg:#a9cfd0',
            'select-checked': 'fg:#000000 bg:#b0e2ff bold',
            'select-selected': 'fg:#000000 bg:#b0e0e6 bold',
            #'dialog shadow': 'bg:#c98982',
            'frame.label': '#884444 bold',
            #'dialog.body label': '#fd8bb6',
            'info': 'fg:#27408b bold',
        })
    )

    #background_task_tune = asyncio.create_task(tune(application))
    background_task_update_spots = asyncio.create_task(
        update_spots(application))

    try:
        await application.run_async()
    finally:
        background_task_update_spots.cancel()
        #background_task_tune.cancel()
    #print("Quitting event loop. Bye.")


if __name__ == "__main__":
    asyncio.run(main())
