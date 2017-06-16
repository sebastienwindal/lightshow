from signal import pause
import led_control


def main():

  # make the light blink a couple of time to signal we are ready
  led_control.start_light_show(led_control.LIGHT_SHOW.TEST)
  

  pause()

if __name__ == '__main__':

  try:
    main()
  except KeyboardInterrupt:
    pass
  finally:
    print "Goodbye"

