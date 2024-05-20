# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 YA-androidapp(https://github.com/yzkn) All rights reserved.

from machine import Pin, Timer
from math import floor
from picounicorn import PicoUnicorn


# Const
RED_MINUTES   = 1
GREEN_MINUTES = 1

# Var
picounicorn = PicoUnicorn()

w = picounicorn.get_width()
h = picounicorn.get_height()
total = w * h

RED_SECONDS   = RED_MINUTES * 60
GREEN_SECONDS = RED_MINUTES * 60

count = 0
state = "idle"


loopTimer = Timer()


def display_binary(value, row, offset, color):
    binary_str = "{0:8b}".format(value)
    for x in range(0, 8):
        if binary_str[x] == '1':
            picounicorn.set_pixel(x+offset, row, color[0], color[1], color[2])
        else:
            picounicorn.set_pixel(x+offset, row, int(color[0] / 10), int(color[1] / 10), int(color[2] / 10))


def show_ready():
    #Red
    display_binary(RED_MINUTES, 0, 0, (100, 0, 0))
        
    #Green
    display_binary(GREEN_MINUTES, 0, 8, (0, 100, 0))

    # READY
    r, g, b = (0, 100, 90)
    xy = [
        (0, 1), (1, 1),                 (4, 1), (5, 1),                 (8, 1),         (10, 1), (11, 1),          (13, 1),          (15, 1),
        (0, 2),         (2, 2),         (4, 2),                 (7, 2),         (9, 2), (10, 2),          (12, 2), (13, 2),          (15, 2),
        (0, 3), (1, 3), (2, 3),         (4, 3), (5, 3),         (7, 3),         (9, 3), (10, 3),          (12, 3),          (14, 3),         
        (0, 4), (1, 4),                 (4, 4),                 (7, 4), (8, 4), (9, 4), (10, 4),          (12, 4),          (14, 4),         
        (0, 5),         (2, 5),         (4, 5),                 (7, 5),         (9, 5), (10, 5),          (12, 5),          (14, 5),
        (0, 6),         (2, 6),         (4, 6), (5, 6),         (7, 6),         (9, 6), (10, 6), (11, 6),                   (14, 6),
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
            show_ready()


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
    show_ready()


def button(timer):
    if picounicorn.is_pressed(picounicorn.BUTTON_A) and state != "active":
        pomodoro_start()
        
    if picounicorn.is_pressed(picounicorn.BUTTON_B) and state != "idle":
        pomodoro_reset()


def pomodoro_init():
    print("pomodoro_init()")
    loopTimer.init(freq=(total / RED_SECONDS), mode=Timer.PERIODIC, callback=loop)
    
    show_ready()
    
    ButtonTimer = Timer()
    ButtonTimer.init(freq=50.0, mode=Timer.PERIODIC, callback=button)

if __name__ == "__main__":
    pomodoro_init()