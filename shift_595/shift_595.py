"""
A library that allows simple access to 74HC595 shift registers on a Raspberry Pi using any digital I/O pins.
"""

import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)

version = "0.2"
version_info = (0, 2)

# Define MODES
ALL = -1
HIGH = 1
LOW = 0


def delay(millis):
    """
    Used for creating a delay between commands
    """
    millis_to_seconds = float(millis) / 1000
    return sleep(millis_to_seconds)


class SN74x595:
    # is used to store states of all pins
    _registers = list()

    # How many of the shift registers - you can change them with shiftRegisters method
    _number_of_shiftregisters = 2

    def __init__(self, ser_pin, rclk_pin, srclk_pin, registersCount=2):
        self._SER_pin = ser_pin
        self._RCLK_pin = rclk_pin
        self._SRCLK_pin = srclk_pin
        self._number_of_shiftregisters = registersCount

        GPIO.setup(ser_pin, GPIO.OUT)
        GPIO.setup(rclk_pin, GPIO.OUT)
        GPIO.setup(srclk_pin, GPIO.OUT)

    def startupMode(self, mode, execute=False):
        """
        Allows the user to change the default state of the shift registers outputs
        """
        if isinstance(mode, int):
            if mode is HIGH or mode is LOW:
                self._all(mode, execute)
            else:
                raise ValueError("The mode can be only HIGH or LOW or Dictionary with specific pins and modes")
        elif isinstance(mode, dict):
            for pin, mode in mode.iteritems():
                self._set_pin(pin, mode)
            if execute:
                self._execute()
        else:
            raise ValueError("The mode can be only HIGH or LOW or Dictionary with specific pins and modes")

    def shiftRegisters(self, num):
        """
        Allows the user to define the number of shift registers are connected
        """
        self._number_of_shiftregisters = num
        self._all(LOW)

    def digitalWrite(self, pin, mode):
        """
        Allows the user to set the state of a pin on the shift register
        """
        if pin == ALL:
            self._all(mode)
        else:
            if len(self._registers) == 0:
                self._all(LOW)

            self._set_pin(pin, mode)
        self._execute()

    def _all_pins(self):
        return self._number_of_shiftregisters * 8

    def _all(self, mode, execute=True):
        all_shr = self._all_pins()

        for pin in range(0, all_shr):
            self._set_pin(pin, mode)
        if execute:
            self._execute()

        return self._registers

    def _set_pin(self, pin, mode):
        try:
            self._registers[pin] = mode
        except IndexError:
            self._registers.insert(pin, mode)

    def _execute(self):
        all_pins = self._all_pins()
        GPIO.output(self._RCLK_pin, GPIO.LOW)

        for pin in range(all_pins - 1, -1, -1):
            GPIO.output(self._SRCLK_pin, GPIO.LOW)

            pin_mode = self._registers[pin]

            GPIO.output(self._SER_pin, pin_mode)
            GPIO.output(self._SRCLK_pin, GPIO.HIGH)

        GPIO.output(self._RCLK_pin, GPIO.HIGH)

