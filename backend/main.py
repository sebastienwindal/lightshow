from signal import pause
from time import sleep
import threading
import led_control
import lcd_control
import rest_server


frequency = 1
mask = 0x00
light_show_str = ""

def bottom_str():
  freq_str = str(frequency) + "Hz"
  for i in range(0, 8-len(freq_str)):
    freq_str += " "
  m = 0x80
  while m != 0:
    if mask & m == 0:
      freq_str += "0"
    else:
      freq_str += "1"
    m >>= 1
  return freq_str

###############################
# LED events
  
def light_show_started(light_show):
  global light_show_str
  light_show_str = light_show.pretty_description()
  
def light_show_completed(light_show):
  global light_show_str
  if light_show.id == led_control.LIGHT_SHOW.INIT:
    light_show_str = "ready"   

def light_show_frequency_changed(freq):
  global frequency
  frequency = freq
  
def light_show_led_changed(m):
  global mask
  mask = m

#####################################
# REST server callback overrides

def status_off_requested():
  off_light_show = led_control.get_light_show(led_control.LIGHT_SHOW.OFF)
  if off_light_show != None:
    led_control.start_light_show(off_light_show.id)

def status_manual_request():
  manual_light_show = led_control.get_light_show(led_control.LIGHT_SHOW.MANUAL)
  if manual_light_show != None:
    led_control.start_light_show(manual_light_show.id)
       
def frequency_requested(freq):
  led_control.set_frequency(freq)
  
####

def lcd_worker():
  while True:
    lcd_control.lcd_string(bottom_str(), lcd_control.LCD_LINE_2)
    lcd_control.lcd_string(light_show_str, lcd_control.LCD_LINE_1)
    sleep(0.05)

    
def rest_worker():
  rest_server.server.run()

  
def main():
  lcd_control.lcd_init()

  led_control.start_light_show(led_control.LIGHT_SHOW.INIT)

  led_control.event_light_show_started.append(light_show_started)
  led_control.event_light_show_completed.append(light_show_completed)
  led_control.event_light_show_frequency_changed.append(light_show_frequency_changed)
  led_control.event_light_show_led_changed.append(light_show_led_changed)

  rest_server.status_off_requested = status_off_requested
  rest_server.status_manual_requested = status_manual_request
  rest_server.frequency_requested = frequency_requested
  
  t = threading.Thread(target=lcd_worker)
  t.daemon = True
  t.start()

  server_thread = threading.Thread(target=rest_worker)
  server_thread.daemon = True
  server_thread.start()
  
  pause()

  
if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    pass
  finally:
    print("Goodbye")
    lcd_control.lcd_clear()

