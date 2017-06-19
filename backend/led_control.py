from gpiozero import LED, Button
from time import sleep
from random import random
from random import uniform
import threading
import json
import event
from event import Event
from enum import Enum

leds = [ LED(4), LED(5), LED(6), LED(13), LED(16), LED(17), LED(27), LED(22) ]
top_button = Button(24)
bottom_button = Button(23)

initial_show_id = 100
current_show_id = initial_show_id
frequency = 1 # Hz
led_mask = 0

# events

event_light_show_started = Event()
event_light_show_completed = Event()
event_light_show_frequency_changed = Event()
event_light_show_led_changed = Event()

def light_show_frequency_changed(frequency):
    print("Frequency set to ", frequency, "Hz")

def light_show_started(show):
    print("Light show ", show.id, " started")

def light_show_completed(show):
    print("Light show ", show.id, " completed")

def light_show_mask_changed(m):
    print(m)
        
event_light_show_started.append(light_show_started)
event_light_show_completed.append(light_show_completed)
event_light_show_frequency_changed.append(light_show_frequency_changed)
event_light_show_led_changed.append(light_show_mask_changed)

# light show definitions

class LIGHT_SHOW(object):
    ALL_ON = 100
    OFF = 101
    ALL_BLINKING = 102
    CYCLING_ONE = 103 # one at a time
    CYCLING_TWO = 104 # two at a time
    RANDOM_1 = 105
    RANDOM_2 = 106
    RANDOM_3 = 107
    MANUAL = 1
    INIT = 0
        
    def __setattr__(self, *_):
        pass

def random_bitmask(on_probability):
    # compute a current bit mask, each bit/LED has a 75% change of being ON.
    mask = 0x00
    for bitIndex in range(0,len(leds)):
        if random() <= on_probability:
            mask |= (0x01 << bitIndex)
    return mask


LIGHT_SHOW = LIGHT_SHOW()

class LightShow:
    def __init__(self, id, name = None, description = None, led_mask_list = [], system = False, read_only = True):
        self.id = id
        self.name = name
        self.description = description
        self.system = system
        self.read_only = read_only
        self.led_mask_list = led_mask_list

    def pretty_description(self):
        return str(self.id) + " (" + self.name + ")"

class Led:
    def __init__(self, id, on):
        self.id = id
        self.on = on
    
light_show_list = [
    LightShow(LIGHT_SHOW.OFF, "OFF", "All Off", [ 0 ]),
    LightShow(LIGHT_SHOW.ALL_ON, "ON", "All On", [ 0xFF ]),
    LightShow(LIGHT_SHOW.ALL_BLINKING, "BLINK ALL", "All LEDs blinking simultaneously", [ 0xFF, 0x00 ]),
    LightShow(LIGHT_SHOW.CYCLING_ONE, "INCR ONE", "Showing all LEDs in order, one at a time", [0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80 ]),
    LightShow(LIGHT_SHOW.CYCLING_TWO, "INCR TWO", "Showing all LEDs in order, two at a time", [ 0b0100000011000000 >> i for i in range(0,8) ]),
    LightShow(LIGHT_SHOW.RANDOM_1, "RAND 1", "Showing random LEDs, 50% change of being ON", [ random_bitmask(0.5) for i in range(0,200)]),
    LightShow(LIGHT_SHOW.RANDOM_2, "RAND 2", "Random light show, 90% chance of LED being ON", [ random_bitmask(0.9) for i\
                                                                                                  in range(0,200)]),
    LightShow(LIGHT_SHOW.RANDOM_3, "RAND 3", "Random light show, natural strategy"),
    LightShow(LIGHT_SHOW.INIT, "INIT", "Initialization LED sequence",  [0xFF, 0xFF, 0x00, 0xFF, 0x00], True),
    LightShow(LIGHT_SHOW.MANUAL, "MANUAL", "Light show is in manual mode", [0x00], True)
]

light_show_dict = {}

for show in light_show_list:
    light_show_dict[show.id] = show

def delete_light_show(show):
    
    if current_show_id == show.id:
        # the current show is being deleted, move back to off
        start_light_show(LIGHT_SHOW.OFF)
        
    light_show_list.remove(show)
    del light_show_dict[show.id]

def create_light_show(name, description, led_masks_list):
    print(led_masks_list)
    show_id = get_unique_light_show_id()
    light_show = LightShow(show_id, name, description, led_masks_list, False, False)
    light_show_list.append(light_show)
    light_show_dict[light_show.id] = light_show
    return light_show

def get_unique_light_show_id():
    shows = sorted(light_show_list, key=lambda show: show.id, reverse=True)
    return shows[0].id + 1

def get_light_show(id):
    if id in light_show_dict: 
        return light_show_dict[id]
    return None

def get_light_shows():
    return [show for show in light_show_list if not show.system]

def get_led_mask():
    return led_mask

def set_led_mask(mask):
    litup(mask)    
    return mask

def get_led(led_index):
    if led_index >= len(leds) or led_index < 0:
        return None
    m = 0x01 < led_index
    on = (m & led_mask) > 0
    return Led(led_index, on)

def get_leds():
    arr = []
    m = 0x01
    for i in range(0, len(leds)):
        on = (m & led_mask) > 0
        led = Led(i, on)
        arr.append(led)
        m = m << 1
    return arr

def turn_led_off(led_index):
    global led_mask
    if led_index >= len(leds) or led_index < 0:
        return None
    led = leds[led_index]
    led_mask &= (0x01 << led_index) ^ 0xFF
    event_light_show_led_changed(led_mask)
    led.off()
    return Led(led_index, False)

def turn_led_on(led_index):
    global led_mask
    if led_index >= len(leds) or led_index < 0:
        return None
    led = leds[led_index]
    led_mask |= (0x01 << led_index)
    event_light_show_led_changed(led_mask)
    led.on()
    return Led(led_index, True)
    
def litup(mask):
    global led_mask
    for index in range(0, len(leds)):
        single_led_mask = 0x01 << index
        led = leds[index]
        if (mask & single_led_mask) > 0:
            led.on()
        else:
            led.off()
    led_mask = mask
    event_light_show_led_changed(mask)

def next_show_id():
    next_show_id = current_show_id + 1
    if next_show_id in light_show_dict:
        if not light_show_dict[next_show_id].system:
            return next_show_id
    return initial_show_id
    
def top_button_pressed():
    print("top button pressed")
    start_light_show(next_show_id())
     
def bottom_button_pressed():
    freq = frequency
    if freq < 1:
        freq += .2
    else:
        freq += 1
        
    if freq > 10:
        freq = 0.2

    set_frequency(freq)

def set_frequency(freq):
    global frequency
    frequency = freq
    event_light_show_frequency_changed(frequency)
    
top_button.when_pressed = top_button_pressed 
bottom_button.when_pressed = bottom_button_pressed

    
def light_show(show_id, pattern, number_repetitions):
    event_light_show_started(light_show_dict[show_id])
    
    global current_show_id
    current_show_id = show_id
    num = 0
    while num < number_repetitions:
        for index in range(0, len(pattern)):
            if current_show_id != show_id:
                event_light_show_completed(light_show_dict[show_id])
                return
            litup(pattern[index])
            sleep(1.0/frequency)
            num += 1
    event_light_show_completed(light_show_dict[show_id])

    
def led_show(show_id, led_index, on_time_min, on_time_max, off_time_min, off_time_max):
    global current_show_id
    global led_mask

    event_light_show_started(light_show_dict[show_id])
    
    current_show_id = show_id
    on_time = uniform(on_time_min, on_time_max)
    off_time = uniform(off_time_min, off_time_max)

    while current_show_id == show_id:
        turn_led_on(led_index)
        sleep(on_time/frequency)
        if current_show_id != show_id:
            event_light_show_completed(light_show_dict[show_id])
            return

        turn_led_off(led_index)
        sleep(off_time/frequency)
    event_light_show_completed(light_show_dict[show_id])



def light_show_worker(light_show_id):
    FOREVER = 1000000000

    show = get_light_show(light_show_id)
    
    if show.system:
        light_show(light_show_id, show.led_mask_list, 1)
        return

    # this one is special
    if light_show_id == LIGHT_SHOW.RANDOM_3:
        event_light_show_started(light_show_dict[light_show_id])
        for led_index in range(0,len(leds)):
            t = threading.Thread(target=led_show, args=(light_show_id, led_index, 5, 10, 1, 2))
            t.start()
        return

    light_show(light_show_id, show.led_mask_list, FOREVER)
    
            
def start_light_show(index):
    t = threading.Thread(target=light_show_worker, args=(index,))
    t.daemon = True
    t.start()
