import led_control
import dist_sensor
import RPi.GPIO as GPIO
from time import sleep

import settings

status_leds_controller = led_control.make_led_panel(controller_config=settings.SHIFT_595_STATUS__DEFAULT_CONFIG,
                                                    led_id_convert_func=led_control.status_led_id_convert)

errors_leds_controller = led_control.make_led_panel(controller_config=settings.SHIFT_595_ERROR__DEFAULT_CONFIG,
                                                    led_id_convert_func=led_control.default_led_id_convert)

#status_leds_controller.test_leds()

# print(repr(status_leds_controller))

# for led in status_leds_controller:
#     led.state = led_control.HIGH

# print('leds: ', len(status_leds_controller))


status_leds_controller[0] = led_control.LOW

mux = dist_sensor.make_mux()

print(mux)

mux.measure_distance_on_sensor_num(0)

print(mux)

# GPIO.output(15, 1)
# GPIO.output(16, 1)
# GPIO.output(18, 1)
# GPIO.output(22, 1)
# 
# GPIO.output(11, 0)
# sleep(20)



# mux.select_sensor(0)
# mux.send_trigger(pulse_length=5)
