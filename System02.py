# http://python-3-patterns-idioms-test.readthedocs.io/en/latest/StateMachine.html

# sys.path += ['../stateMachine', '../mouse']
import time
import signal

import RPi.GPIO as GPIO

import led_control
import dist_sensor

GPIO.setmode(GPIO.BOARD)


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

led_control.diag_leds()

continue_reading = True


def measure_all_sensors():
    pass


try:
    while continue_reading:
        # print("000000")

        led_control.blink_led(ledCurrentNum)
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
