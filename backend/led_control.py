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
led_mask = 0

class LIGHT_SHOW(object):
    OFF = 0
    ALL_ON = 1
    ALL_BLINKING = 2
    CYCLING_ONE = 3 # one at a time
    CYCLING_TWO = 4 # two at a time
    RANDOM_1 = 5
    RANDOM_2 = 6
    RANDOM_3 = 7
    INIT = 100000
        
    def __setattr__(self, *_):
        pass

LIGHT_SHOW = LIGHT_SHOW()

class LightShow:
    def __init__(self, id, name = None, description = None):
        self.id = id
        self.name = name
        self.description = description

    def pretty_description(self):
        return str(self.id) + " (" + self.name + ")"

light_show_list = [
    LightShow(LIGHT_SHOW.OFF, "OFF", "All Off"),
    LightShow(LIGHT_SHOW.ALL_ON, "ON", "All On"),
    LightShow(LIGHT_SHOW.ALL_BLINKING, "BLINK ALL", "All LEDs blinking simultaneously"),
    LightShow(LIGHT_SHOW.CYCLING_ONE, "INCR ONE", "Showing all LEDs in order, one at a time"),
    LightShow(LIGHT_SHOW.CYCLING_TWO, "INCR TWO", "Showing all LEDs in order, two at a time"),
    LightShow(LIGHT_SHOW.RANDOM_1, "RAND 1", "Showing random LEDs, 50% change of being ON"),
    LightShow(LIGHT_SHOW.RANDOM_2, "RAND 2", "Random light show, 90% chance of LED being ON"),
    LightShow(LIGHT_SHOW.RANDOM_3, "RAND 3", "Random light show, natural strategy"),
    LightShow(LIGHT_SHOW.INIT, "INIT")
]

light_show_dict = {}

for show in light_show_list:
    light_show_dict[show.id] = show

def litup(mask):
    for index in xrange(0, len(leds)):
        single_led_mask = 0x01 << index
	led = leds[index]
        if (mask & single_led_mask) > 0:
            led.on()
	else:
	    led.off()
    led_mask = mask
    light_show_mask_changed(mask)

num_button_presses = 0
def top_button_pressed():
    print("top button pressed")
    global num_button_presses
    num_button_presses = num_button_presses + 1
    light_show_index = num_button_presses % 8   
    start_light_show(light_show_index)
 
def bottom_button_pressed():
    global frequency
    if frequency < 1:
        frequency += .2
    else:
        frequency += 1
        
    if frequency > 10:
        frequency = 0.2

    light_show_frequency_changed(frequency)
    
top_button.when_pressed = top_button_pressed 
bottom_button.when_pressed = bottom_button_pressed

def light_show_frequency_changed(frequency):
    print "Frequency set to ", frequency, "Hz"

def light_show_started(show):
    print "Light show ", show.id, " started"

def light_show_completed(show):
    print "Light show ", show.id, " completed"
    
def light_show(show_id, pattern, number_repetitions):
    light_show_started(light_show_dict[show_id])
    
    global current_show
    current_show = show_id
    num = 0
    while num < number_repetitions:
	for index in xrange(0, len(pattern)):
            if current_show != show_id:
                light_show_completed(light_show_dict[show_id])
                return
            litup(pattern[index])
            sleep(1.0/frequency)
            num += 1
    light_show_completed(light_show_dict[show_id])

def light_show_mask_changed(m):
    print(m)
    
def led_show(show_id, led_index, on_time_min, on_time_max, off_time_min, off_time_max):
    global current_show
    global led_mask

    current_show = show_id
    on_time = uniform(on_time_min, on_time_max)
    off_time = uniform(off_time_min, off_time_max)

    while current_show == show_id:
        led = leds[led_index]
        led.on()
        led_mask |= (0x01 << led_index)
        light_show_mask_changed(led_mask)
        sleep(on_time/frequency)
        if current_show != show_id:
            light_show_completed(light_show_dict[show_id])
            return
        led.off()
        led_mask ^= (0x01 << led_index) ^ 0xFF
        
        light_show_mask_changed(led_mask)
        sleep(off_time/frequency)
    light_show_completed(light_show_dict[show_id])
    

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

    if light_show_id == LIGHT_SHOW.INIT:
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
        light_show_started(light_show_dict[light_show_id])
        for led_index in xrange(0,len(leds)):            
            t = threading.Thread(target=led_show, args=(light_show_id, led_index, 5, 10, 1, 2))
            t.start()
            
def start_light_show(index):
    t = threading.Thread(target=light_show_worker, args=(index,))
    t.start()
