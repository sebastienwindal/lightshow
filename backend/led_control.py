from gpiozero import LED, Button
from time import sleep
from random import random
from random import uniform
import threading


leds = [ LED(4), LED(17), LED(27), LED(22), LED(5), LED(6), LED(13), LED(16) ]
top_button = Button(24)
bottom_button = Button(23)

current_show = 0
frequency = 1 # Hz

class LIGHT_SHOW(object):
    OFF = 0
    ALL_ON = 1
    ALL_BLINKING = 2
    CYCLING_ONE = 3 # one at a time
    CYCLING_TWO = 4 # two at a time
    RANDOM_1 = 5
    RANDOM_2 = 6
    RANDOM_3 = 7
    TEST = 100000
        
    def __setattr__(self, *_):
        pass

LIGHT_SHOW = LIGHT_SHOW()

def litup(mask):
    for index in xrange(0, len(leds)):
        single_led_mask = 0x01 << index
	led = leds[index]
        if (mask & single_led_mask) > 0:
            led.on()
	else:
	    led.off()

num_button_presses = 0
def top_button_pressed():
    print("top button pressed")
    global num_button_presses
    num_button_presses = num_button_presses + 1
    light_show_index = num_button_presses % 8
    print "New Light Show:", light_show_index
    start_light_show(light_show_index)
 
def bottom_button_pressed():
    global frequency
    print("bottom button pressed")
    frequency *= 2
    if frequency > 10:
        frequency = 0.25
    
    
top_button.when_pressed = top_button_pressed 
bottom_button.when_pressed = bottom_button_pressed

def light_show(show_id, pattern, number_repetitions):
    global current_show
    current_show = show_id
    num = 0
    while num < number_repetitions:
	for index in xrange(0, len(pattern)):
            if current_show != show_id:
                return
            litup(pattern[index])
            sleep(1.0/frequency)
            num += 1


def led_show(show_id, led_index, on_time_min, on_time_max, off_time_min, off_time_max):
    global current_show
    current_show = show_id
    on_time = uniform(on_time_min, on_time_max)
    off_time = uniform(off_time_min, off_time_max)
    
    while current_show == show_id:
        led = leds[led_index]
        led.on()
        sleep(on_time/frequency)
        if current_show != show_id:
            return
        led.off()
        sleep(off_time/frequency)
        

def random_bitmask(on_probability):
    # compute a current bit mask, each bit/LED has a 75% change of being ON.
    mask = 0x00
    for bitIndex in xrange(0,len(leds)):
        if random() <= on_probability:
            mask |= (0x01 << bitIndex)
    return mask


def light_show_worker(light_show_id):
    FOREVER = 1000000000

    if light_show_id == LIGHT_SHOW.OFF:
        light_show(light_show_id, [ 0x00 ], 1)

    if light_show_id == LIGHT_SHOW.ALL_ON:
        light_show(light_show_id, [ 0xFF ], 1)

    if light_show_id == LIGHT_SHOW.TEST:
        light_show(light_show_id, [0xFF, 0x00 ], 3)
        
    if light_show_id == LIGHT_SHOW.ALL_BLINKING:
        light_show(light_show_id, [ 0xFF, 0x00 ], FOREVER)

    if light_show_id == LIGHT_SHOW.CYCLING_ONE:
        light_show(light_show_id, [ 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80 ], FOREVER)

    if light_show_id == LIGHT_SHOW.CYCLING_TWO:
        arr = []
        mask = 0x0003
        while mask <= 0x00C0:
            arr.append(mask)
            mask = mask << 1
        light_show(light_show_id, arr, FOREVER)

    if light_show_id == LIGHT_SHOW.RANDOM_1:
        arr = [ 0xFF ]
        for i in range(600):
            arr.append(random_bitmask(0.5))
        light_show(light_show_id, arr, FOREVER)

    if light_show_id == LIGHT_SHOW.RANDOM_2:
        arr = [ 0xFF ]
        for i in range(600):
            arr.append(random_bitmask(0.9))
        light_show(light_show_id, arr, FOREVER)

    if light_show_id == LIGHT_SHOW.RANDOM_3:
        for led_index in xrange(0,len(leds)):            
            t = threading.Thread(target=led_show, args=(light_show_id, led_index, 4.5, 10.5, 0.5, 1.5))
            t.start()

            
def start_light_show(index):
    t = threading.Thread(target=light_show_worker, args=(index,))
    t.start()
