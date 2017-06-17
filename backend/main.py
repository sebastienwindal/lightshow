from signal import pause
from time import sleep
import threading
import led_control
import lcd_control

frequency = 1
mask = 0x00
light_show_str = ""

def bottom_str():
  freq_str = str(frequency) + "Hz"
  for i in xrange(0, 8-len(freq_str)):
    freq_str += " "

  m = 0x80
  while m != 0:
    if mask & m == 0:
      freq_str += "0"
    else:
      freq_str += "1"
    m >>= 1

  return freq_str

  
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

  
def light_show_mask_changed(m):
  global mask
  mask = m
  
  
def lcd_worker():
  while True:
    lcd_control.lcd_string(bottom_str(), lcd_control.LCD_LINE_2)
    lcd_control.lcd_string(light_show_str, lcd_control.LCD_LINE_1)
    sleep(0.05)

    
def main():
  lcd_control.lcd_init()

  # make the light blink a couple of time to signal we are ready
  led_control.start_light_show(led_control.LIGHT_SHOW.INIT)
  led_control.light_show_started = light_show_started  
  led_control.light_show_completed = light_show_completed
  led_control.light_show_frequency_changed = light_show_frequency_changed
  led_control.light_show_mask_changed = light_show_mask_changed

  t = threading.Thread(target=lcd_worker)
  t.daemon = True
  t.start()
  
  pause()

  
if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    pass
  finally:
    print "Goodbye"
    lcd_control.lcd_clear()

