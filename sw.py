#!/usr/bin/env python3

from gpiozero import Button
import pyautogui
import time

gpio_sw =14
sw = Button(gpio_sw, pull_up=False)

prev = False
while True:
    time.sleep(0.1)
    if not prev and sw.is_pressed:
        pyautogui.press("a")
    prev = sw.is_pressed