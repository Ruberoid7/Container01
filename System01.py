import time
#from iothub_client import IoTHubClient, IoTHubClientError, IoTHubTransportProvider, IoTHubClientResult
#from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue
import RPi.GPIO as GPIO
#from shiftpi import HIGH, LOW, digitalWrite, delay, ALL, shiftRegisters, pinsSetup

from shift_595 import shiftpi2
from shift_595.shiftpi2 import HIGH, LOW

#import shiftpi as STATUS_LEDS
#import shiftpi as DIAG_LEDS

import signal

#ALL  = -1
#HIGH = 1
#LOW  = 0

#GPIO.setmode(GPIO.BCM)
GPIO.setmode(GPIO.BOARD)

    
#_PIN_ADDR_0 = 22
_PIN_ADDR_0 = 15
#_PIN_ADDR_1 = 23
_PIN_ADDR_1 = 16
#_PIN_ADDR_2 = 24
_PIN_ADDR_2 = 18
#_PIN_ADDR_3 = 25
_PIN_ADDR_3 = 22

#_PIN_TRIG = 17
_PIN_TRIG = 11

#_PIN_ECHO = 27
_PIN_ECHO = 13

_PIN_SHIFT_STATUS_SER = 40
_PIN_SHIFT_STATUS_RCLK = 38
_PIN_SHIFT_STATUS_SRCLK = 37

_PIN_SHIFT_ERROR_SER = 31
_PIN_SHIFT_ERROR_RCLK = 33
_PIN_SHIFT_ERROR_SRCLK = 35


_IOT_HUB_CONN_STRING = 'HostName=uralchem-iot-hub.azure-devices.net;DeviceId=RaspberryPi_test_button;SharedAccessKey=QqLFpZw7rtElA87DZ/mx2dJ1KaCchA/wTFLgU1+EEI8='
_IOT_HUB_MSG_TXT = "{\"deviceId\": \"RaspberryPi_test_button""\",\"distance_1\": %f,\"distance_2\": %f,\"distance_3\": %f,\"distance_4\": %f,\"distance_5\": %f,\"distance_6\": %f,\"distance_7\": %f,\"distance_8\": %f,\"distance_9\": %f,\"distance_10\": %f}"

status_leds = shiftpi2.SN74x595(ser_pin = _PIN_SHIFT_STATUS_SER, rclk_pin = _PIN_SHIFT_STATUS_RCLK, srclk_pin = _PIN_SHIFT_STATUS_SRCLK)
diag_leds = shiftpi2.SN74x595(ser_pin = _PIN_SHIFT_ERROR_SER, rclk_pin = _PIN_SHIFT_ERROR_RCLK, srclk_pin = _PIN_SHIFT_ERROR_SRCLK)

def blink_led(register, num):
    register.digitalWrite(num, HIGH)
    time.sleep(0.5)
    register.digitalWrite(num, LOW)
    time.sleep(0.2)
    register.digitalWrite(num, HIGH)
    time.sleep(0.5)
    register.digitalWrite(num, LOW)
    time.sleep(0.2)

def displayStates():
    print("Test")




continue_reading = True

# Capture SIGINT for cleanup when the script is aborted
def end_read(signal,frame):
    global continue_reading
    print("Ctrl+C captured, ending read.")
    continue_reading = False
    GPIO.cleanup()

# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

ledStartNum = 0
ledEndNum = 15
ledCurrentNum = ledStartNum

#status_leds.digitalWrite(ALL, HIGH)
#diag_leds.digitalWrite(ALL, HIGH)

time.sleep(3)

try:
    while continue_reading:
        #print("000000")

        get_distance(2)
        
        blink_led(status_leds, ledCurrentNum)
        blink_led(diag_leds, ledCurrentNum)
        
        time.sleep(0.5)
        
        ledCurrentNum = ledCurrentNum + 1
        if ledCurrentNum > ledEndNum:
            ledCurrentNum = ledStartNum

        displayStates()
      

except KeyboardInterrupt:
    print('KeyboardInterrupt')
    end_read()

GPIO.cleanup()
