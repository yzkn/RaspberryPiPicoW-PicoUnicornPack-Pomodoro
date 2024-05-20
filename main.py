# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 YA-androidapp(https://github.com/yzkn) All rights reserved.
from machine import Pin
from pimoroni import Button
from picounicorn import PicoUnicorn
import network
import socket
import time
import uasyncio as asyncio
import WIFI_CONFIG

from machine import Pin, Timer
from math import floor
from picounicorn import PicoUnicorn


# Const
WEB_PORT = 80

RED_MINUTES   = 25
GREEN_MINUTES = 5


# Var
picounicorn = PicoUnicorn()
w = picounicorn.get_width()
h = picounicorn.get_height()
total = w * h

RED_SECONDS   = RED_MINUTES * 60
GREEN_SECONDS = RED_MINUTES * 60

count = 0
ipaddrlast = 0
state = "idle"

led = Pin("LED", Pin.OUT, value=0)

WEB_SOURCE = """<!DOCTYPE html>
<html>
    <head> <title>Pico W</title> </head>
    <body> <h1>Pico W</h1>
        <p>%s</p>
    </body>
</html>
"""


# Function
def display_binary(value, row, offset, color, wide=False):
    binary_str = "{0:16b}".format(value) if wide else "{0:8b}".format(value)
    for x in range(0, 16 if wide else 8):
        if binary_str[x] == '1':
            picounicorn.set_pixel(x+offset, row, color[0], color[1], color[2])
        else:
            picounicorn.set_pixel(x+offset, row, int(color[0] / 10), int(color[1] / 10), int(color[2] / 10))


def show_ready(ipaddrlast):
    #Red
    display_binary(RED_MINUTES, 0, 0, (100, 0, 0))

    #Green
    display_binary(GREEN_MINUTES, 0, 8, (0, 100, 0))

    #Blue
    display_binary(ipaddrlast, 6, 0, (0, 0, 100), True)

    # READY
    r, g, b = (0, 100, 90)
    xy = [
        (0, 1), (1, 1),                 (4, 1), (5, 1),                 (8, 1),         (10, 1), (11, 1),          (13, 1),          (15, 1),
        (0, 2),         (2, 2),         (4, 2),                 (7, 2),         (9, 2), (10, 2),          (12, 2), (13, 2),          (15, 2),
        (0, 3), (1, 3), (2, 3),         (4, 3), (5, 3),         (7, 3),         (9, 3), (10, 3),          (12, 3),          (14, 3),         
        (0, 4), (1, 4),                 (4, 4),                 (7, 4), (8, 4), (9, 4), (10, 4),          (12, 4),          (14, 4),         
        (0, 5),         (2, 5),         (4, 5), (5, 5),         (7, 5),         (9, 5), (10, 5), (11, 5),                   (14, 5),
    ]

    for x, y in xy:
        picounicorn.set_pixel(x, y, r, g, b)


def fill(r, g, b):
    for x in range(w):
        for y in range(h):
            picounicorn.set_pixel(x, y, r, g, b)
    

def loop(timer):
    global count
    global state
    
    if state == "active":
        if count < total:
            x = count % w
            y = floor(count / w)
            picounicorn.set_pixel(x, y, 100, 0, 0)
            count = count + 1
        else:
            state = "break"
            fill(0,100,0)
            loopTimer.init(freq=(total / GREEN_SECONDS), mode=Timer.PERIODIC, callback=loop)
    
    
    if state == "break":
        if count > 0:
            count = count - 1
            x = count % w
            y = floor(count / w)
            picounicorn.set_pixel(x, y, 0, 0, 0)
        else:
            state = "idle"
            show_ready(ipaddrlast)


# Event handler
def pomodoro_start():
    global count
    global state
    
    print("START")
    count = 0
    state = "active"
    fill(0,0,0)


def pomodoro_reset():
    global count
    global state
    
    print("RESET")
    state = "idle"
    fill(0,0,0)
    show_ready(ipaddrlast)


def button(timer):
    if picounicorn.is_pressed(picounicorn.BUTTON_A) and state != "active":
        pomodoro_start()
        
    if picounicorn.is_pressed(picounicorn.BUTTON_B) and state != "idle":
        pomodoro_reset()


# WiFi
ssid = WIFI_CONFIG.SSID
password = WIFI_CONFIG.PSK

print(ssid, password)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)


max_wait = 10
while max_wait > 0:
    if wlan.isconnected():
        break
    max_wait -= 1
    print("waiting for connection...")
    time.sleep(1)
    wlan.connect(ssid, password)
    time.sleep(2)

if wlan.status() != 3:
    print(wlan.ifconfig())
    raise RuntimeError("network connection failed")
else:
    print("connected")
    status = wlan.ifconfig()
    print( "ip = " + status[0] )
    time.sleep(0.5)

addr = socket.getaddrinfo("0.0.0.0", WEB_PORT)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)
stateis = ""
print("listening on", addr)


idx = str(status[0]).rfind('.')
addr_last_num = int(str(status[0])[idx+1:])


loopTimer = Timer()
loopTimer.init(freq=(total / RED_SECONDS), mode=Timer.PERIODIC, callback=loop)

show_ready(addr_last_num)
    
ButtonTimer = Timer()
ButtonTimer.init(freq=5.0, mode=Timer.PERIODIC, callback=button)


# Listen for connections
while True:
    try:
        cl, addr = s.accept()
        print("client connected from", addr)
        request = cl.recv(1024)
        print(request)

        request = str(request)
        print( "request = " + request)
        pmd_start = request.find("/start")
        pmd_reset = request.find("/reset")
        led_on = request.find("/led_on")
        led_off = request.find("/led_off")
        print( "pmd_start = " + str(pmd_start))
        print( "pmd_reset = " + str(pmd_reset))
        print( "led on = " + str(led_on))
        print( "led off = " + str(led_off))
        
        if pmd_start == 6:
            print("pmd_start")
            pomodoro_start()

        if pmd_reset == 6:
            print("pmd_reset")
            pomodoro_reset()

        if led_on == 6:
            print("led on")
            led.value(1)
            stateis = "LED is ON"
            time.sleep(0.5)

        if led_off == 6:
            print("led off")
            led.value(0)
            stateis = "LED is OFF"
            time.sleep(0.5)

        response = WEB_SOURCE % stateis

        cl.send("HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n")
        cl.send(response)
        cl.close()

    except OSError as e:
        cl.close()
        print("connection closed")
