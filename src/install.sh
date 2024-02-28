#!/bin/bash -x

pip3 install -r requirements.txt
pip3 install --upgrade --force-reinstall  git+https://github.com/on3ure/python-prompt-toolkit

mkdir ~/bin

cp dxsummit.py ~/bin/dxsummit
chmod +x ~/bin/dxsummit

cp qrz.py ~/bin/qrz
chmod +x ~/bin/qrz

cp qte.py ~/bin/qte
chmod +x ~/bin/qte
