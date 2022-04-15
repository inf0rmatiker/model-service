#!/bin/bash

python3.8 -m venv . && chmod +x ./bin/activate && ./bin/activate;
./bin/pip3 install --upgrade pip;
./bin/pip3 install -r requirements.txt;