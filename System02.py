# http://python-3-patterns-idioms-test.readthedocs.io/en/latest/StateMachine.html

import sys

sys.path += ['../stateMachine', '../mouse']

import random
import time
import signal
import collections

import RPi.GPIO as GPIO
import shiftpi2
from shiftpi2 import HIGH, LOW, ALL
from settings import *

GPIO.setmode(GPIO.BOARD)

from dist_sensor import *

status_leds = shiftpi2.SN74x595(ser_pin=PIN_SHIFT_STATUS_SER, rclk_pin=PIN_SHIFT_STATUS_RCLK,
                                srclk_pin=PIN_SHIFT_STATUS_SRCLK)
diag_leds = shiftpi2.SN74x595(ser_pin=PIN_SHIFT_ERROR_SER, rclk_pin=PIN_SHIFT_ERROR_RCLK,
                              srclk_pin=PIN_SHIFT_ERROR_SRCLK)

BLINK = 2

# configure leds - may be needed in time
LedConfig = collections.namedtuple('LedConfig', ['StatusNum', 'ErrorNum'])


def no_op(num):
    return num


class LedControl(object):
    # control single led

    def __init__(self, uid, state=HIGH):
        self._uid = uid
        self_last_state = self._current_state = state

    def __repr__(self):
        return self.__class__.__name__ + " # " + str(self.uid)

    @property
    def state(self):
        return self._current_state

    @state.setter
    def state(self, new_state):
        if new_state != HIGH and new_state != LOW and new_state != BLINK:
            raise ValueError('Bad State')

        self._last_state = self._state
        self._current_state = new_state

    @property
    def last_state(self):
        return self._last_state

    @property
    def uid(self):
        return self._uid


class LedControlPanel(object):
    # control led_panel for Sensors

    def __init__(self, number_of_leds=DEFAULT_NUMBER_OF_SENSORS):
        # self._leds = list()

        # create list of leds
        self._leds = [LedControl(led_num) for led_num in range(number_of_leds)]

    def __len__(self):
        return len(self._leds)

    def __get_item__(self, num):
        return self._leds[num]

    def __iter__(self):
        return iter(self._leds)

    @staticmethod
    def get_state_for_led(led):
        return led.state

    def get_state_for_led_num(self, led_num):
        return self[num].state

    @staticmethod
    def set_state_for_led(led, new_state):
        led.state = new_state

    def set_state_for_led_num(self, led_num, new_state):
        self[led_num].state = new_state

    def set_state_for_all(self, new_state=HIGH):
        for led in self:
            self.set_state_for_led(led, new_state)

# TODO: OLD API - must be reimplemented in a class
def get_status_led_id(num):
    return 8 * (num // 5) + num % 5


def get_diag_led_id(num):
    return num


def set_status_led(num, state=HIGH):
    led_id = get_status_led_id(num)
    print('Flash LED: ', led_id, ' for: ', num)
    status_leds.digitalWrite(led_id, state)


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


_IOT_HUB_CONN_STRING = 'HostName=uralchem-iot-hub.azure-devices.net;DeviceId=RaspberryPi_test_button;SharedAccessKey' \
                       '=QqLFpZw7rtElA87DZ/mx2dJ1KaCchA/wTFLgU1+EEI8= '
_IOT_HUB_MSG_TXT = "{\"deviceId\": \"RaspberryPi_test_button""\",\"distance_1\": %f,\"distance_2\": %f,\"distance_3\": %f,\"distance_4\": %f,\"distance_5\": %f,\"distance_6\": %f,\"distance_7\": %f,\"distance_8\": %f,\"distance_9\": %f,\"distance_10\": %f}"

continue_reading = True


# Capture SIGINT for cleanup when the script is aborted
def end_read(signal, frame):
    global continue_reading
    print("Ctrl+C captured, ending read.")
    continue_reading = False
    # GPIO.cleanup()


# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

ledStartNum = 0
ledEndNum = 9
ledCurrentNum = ledStartNum

status_leds.digitalWrite(ALL, HIGH)
diag_leds.digitalWrite(ALL, HIGH)

time.sleep(3)

status_leds.digitalWrite(ALL, LOW)
diag_leds.digitalWrite(ALL, LOW)

try:
    while continue_reading:
        # print("000000")

        blink_led(ledCurrentNum)
        # blink_led(diag_leds, ledCurrentNum)

        time.sleep(0.5)

        ledCurrentNum = ledCurrentNum + 1
        if ledCurrentNum > ledEndNum:
            ledCurrentNum = ledStartNum

        # displayStates()


except KeyboardInterrupt:
    print('KeyboardInterrupt')
    end_read()

GPIO.cleanup()
