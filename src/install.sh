#!/bin/bash -x

sudo pip3 install -r requirements.txt
sudo pip3 install --upgrade --force-reinstall  git+https://github.com/on3ure/python-prompt-toolki

sudo cp dxsummit.py /usr/bin/dxsummit
sudo chmod +x /usr/bin/dxsummit

sudo cp qrz.py /usr/bin/qrz
sudo chmod +x /usr/bin/qrz
