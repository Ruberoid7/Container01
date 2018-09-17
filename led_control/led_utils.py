import collections
import time

import settings
import shift_595
from shift_595 import HIGH, ALL, LOW

# configure leds - may be needed in time
LedConfig = collections.namedtuple('LedConfig', ['StatusNum', 'ErrorNum'])

status_leds = shift_595.SN74x595(ser_pin=settings.PIN_SHIFT_STATUS_SER, rclk_pin=settings.PIN_SHIFT_STATUS_RCLK,
                                 srclk_pin=settings.PIN_SHIFT_STATUS_SRCLK)
diag_leds = shift_595.SN74x595(ser_pin=settings.PIN_SHIFT_ERROR_SER, rclk_pin=settings.PIN_SHIFT_ERROR_RCLK,
                                        srclk_pin=settings.PIN_SHIFT_ERROR_SRCLK)
TEST = 0

# default led id from led number converter
def default_led_id_convert(num):
    return num

# status led id converter (595 register 4 statuses splited on two simmetric chips for separate disabling)
def status_led_id_convert(num):
    return 8 * (num // 5) + num % 5


# TODO: OLD API - must be reimplemented in a class

def set_status_led(controller, num, state=HIGH):
    led_id = get_status_led_id(num)
    print('Flash LED: ', led_id, ' for: ', num)
    controller.digitalWrite(led_id, state)


def set_diag_led(num, state=HIGH):
    pass
    # diag_leds.digitalWrite(get_diag_led_id(num), state, ' for ', num)


def blink_led(num):
    set_status_led(num, HIGH)
    set_diag_led(num, HIGH)
    time.sleep(0.2)
    set_status_led(num, LOW)
    set_diag_led(num, LOW)
    time.sleep(0.2)
    set_status_led(num, HIGH)
    set_diag_led(num, HIGH)
    time.sleep(0.2)
    set_status_led(num, LOW)
    set_diag_led(num, LOW)
    time.sleep(0.2)


def test_leds():
    status_leds.digitalWrite(ALL, HIGH)
    diag_leds.digitalWrite(ALL, HIGH)

    time.sleep(3)

    status_leds.digitalWrite(ALL, LOW)
    diag_leds.digitalWrite(ALL, LOW)
