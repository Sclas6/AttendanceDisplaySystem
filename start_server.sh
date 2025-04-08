#!/bin/sh

cd /home/kintai/server/
export DISPLAY=:0
screen -S sw -d -m /usr/bin/python sw.py
cd back
screen -S back -d -m /usr/bin/python -m uvicorn main:app --reload --host=172.16.15.7
cd ../front
screen -S front -d -m npm run start