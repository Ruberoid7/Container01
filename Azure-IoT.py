import random
import time
import sys
from iothub_client import IoTHubClient, IoTHubClientError, IoTHubTransportProvider, IoTHubClientResult
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue
import RPi.GPIO as GPIO
import re
import requests
#import config as config
#from telemetry import Telemetry
import MFRC522
import signal
import Adafruit_DHT
import subprocess

from shiftpi import HIGH, LOW, digitalWrite, delay, ALL, shiftRegisters

GPIO.cleanup()

class SN74LS165:
    pulse_time = .000005     # 5 microseconds

    def __init__(self, clock, latch, data, clock_enable, num_chips=1):
        self.latch = latch                 # AKA pload AKA PL, pin 1
        self.clock = clock                 # AKA CP, pin 2
        self.data = data                   # AKA Q7, pin 9
        self.clock_enable = clock_enable   # AKA CE, pin 15

        self.num_chips = num_chips
        self.datawidth = self.num_chips * 8

        GPIO.setup(self.latch, GPIO.OUT)
        GPIO.setup(self.clock, GPIO.OUT)
        GPIO.setup(self.data, GPIO.IN)
        GPIO.setup(self.clock_enable, GPIO.OUT)

    def read_shift_regs(self):
        # Logic copied from the Arduino program.
        # XXX Doesn't make room fo data width for higher numbers of chips.
        GPIO.output(self.clock_enable, GPIO.HIGH)
        GPIO.output(self.latch, GPIO.LOW)
        time.sleep(SN74LS165.pulse_time)
        GPIO.output(self.latch, GPIO.HIGH)
        GPIO.output(self.clock_enable, GPIO.LOW)
        bytes_val = 0
        for i in range(self.datawidth):
            bit = GPIO.input(self.data)
            bytes_val |= bit << (self.datawidth - 1 - i)
            # Pulse the clock: rising edge shifts the next bit.
            GPIO.output(self.clock, GPIO.HIGH)
            time.sleep(SN74LS165.pulse_time)
            GPIO.output(self.clock, GPIO.LOW)
            time.sleep(SN74LS165.pulse_time)
        return bytes_val

# Define Gercon PINs on board
_Gercon_1 = 3
_Gercon_2 = 5
_Gercon_3 = 8
_Gercon_4 = 10
_Gercon_5 = 12
_Gercon_6 = 16

# Define LED PINs on SHIFT register
_LED_Red = 2
_LED_Red_0101 = 12
_LED_Blue_0101 = 13
_LED_Blue_0102 = 14


# Define ECHO PINs on SHIFT register
_TRIG_1 = 1
_TRIG_2 = 2
_TRIG_3 = 3
_TRIG_4 = 4
_TRIG_5 = 5
_TRIG_6 = 6
_TRIG_7 = 7
_TRIG_8 = 9
_TRIG_9 = 10
_TRIG_10 = 11
#_TRIG_1 = _TRIG_2 = _TRIG_3 = _TRIG_4 = _TRIG_5 = _TRIG_6 = _TRIG_7 = _TRIG_8 = _TRIG_9 = _TRIG_10 = 1


# Define GPIOs on board
_ECHO_1 = 37
_ECHO_2 = 35
_ECHO_3 = 33
_ECHO_4 = 31
_ECHO_5 = 29
_ECHO_6 = 32
_ECHO_7 = 15
_ECHO_8 = 13
_ECHO_9 = 11
_ECHO_10 = 7
#_ECHO_1 = _ECHO_2 = _ECHO_3 = _ECHO_4 = _ECHO_5 = _ECHO_6 = _ECHO_7 = _ECHO_8 = _ECHO_9 = _ECHO_10 = 37

# Define GPIOs on board for Shift register
_SER_pin   = 40   #pin 14 on the 75HC595
_RCLK_pin  = 38   #pin 12 on the 75HC595
_SRCLK_pin = 36   #pin 11 on the 75HC595


GPIO.cleanup()
# GPIO mode setup
GPIO.setmode(GPIO.BOARD)
# Configure distance sensor
GPIO.setup(_ECHO_1, GPIO.IN)
GPIO.setup(_ECHO_2, GPIO.IN)
GPIO.setup(_ECHO_3, GPIO.IN)
GPIO.setup(_ECHO_4, GPIO.IN)
GPIO.setup(_ECHO_5, GPIO.IN)
GPIO.setup(_ECHO_6, GPIO.IN)
GPIO.setup(_ECHO_7, GPIO.IN)
GPIO.setup(_ECHO_8, GPIO.IN)
GPIO.setup(_ECHO_9, GPIO.IN)
GPIO.setup(_ECHO_10, GPIO.IN)

#GPIO.setup(_TRIG_1, GPIO.OUT)

# Configure GPIO for Gercon
GPIO.setup(_Gercon_1, GPIO.IN)
GPIO.setup(_Gercon_2, GPIO.IN)
GPIO.setup(_Gercon_3, GPIO.IN)
GPIO.setup(_Gercon_4, GPIO.IN)
GPIO.setup(_Gercon_5, GPIO.IN)
GPIO.setup(_Gercon_6, GPIO.IN)

# Configure GPIO for shift registers
GPIO.setup(_SER_pin, GPIO.OUT)
GPIO.setup(_RCLK_pin, GPIO.OUT)
GPIO.setup(_SRCLK_pin, GPIO.OUT)

TIMEOUT = 24
MINIMUM_POLLING_TIME = 9
MESSAGE_TIMEOUT = 10
RECEIVE_CONTEXT = 0
MESSAGE_COUNT = 0
MESSAGE_SWITCH = True
TWIN_CONTEXT = 0
SEND_REPORTED_STATE_CONTEXT = 0
METHOD_CONTEXT = 0
TEMPERATURE_ALERT = 30.0
RECEIVE_CALLBACKS = 0
SEND_CALLBACKS = 0
BLOB_CALLBACKS = 0
TWIN_CALLBACKS = 0
SEND_REPORTED_STATE_CALLBACKS = 0
METHOD_CALLBACKS = 0
EVENT_SUCCESS = "success"
EVENT_FAILED = "failed"
# chose HTTP, AMQP or MQTT as transport protocol
PROTOCOL = IoTHubTransportProvider.MQTT
CONNECTION_STRING = 'HostName=uralchem-iot-hub.azure-devices.net;DeviceId=RaspberryPi_test_button;SharedAccessKey=QqLFpZw7rtElA87DZ/mx2dJ1KaCchA/wTFLgU1+EEI8='
MSG_TXT = "{\"deviceId\": \"RaspberryPi_test_button""\",\"distance_1\": %f,\"distance_2\": %f,\"distance_3\": %f,\"distance_4\": %f,\"distance_5\": %f,\"distance_6\": %f,\"distance_7\": %f,\"distance_8\": %f,\"distance_9\": %f,\"distance_10\": %f}"

shiftRegisters(3)
# Create an object of the class MFRC522
#MIFAREReader = MFRC522.MFRC522()

continue_reading = True
# Capture SIGINT for cleanup when the script is aborted
def end_read(signal,frame):
    global continue_reading
    print("Ctrl+C captured, ending read.")
    continue_reading = False

# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

def check_internet():
    url='http://www.google.com/'
    timeout=5
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        print("No Internet connection")
        return False

# Blinking with green LED
def blink_green():
    print("Green LED blinking")
    digitalWrite(_LED_Green, HIGH)
    time.sleep(0.5)
    digitalWrite(_LED_Green, LOW)
    time.sleep(0.2)
    digitalWrite(_LED_Green, HIGH)
    time.sleep(0.5)
    digitalWrite(_LED_Green, LOW)
    time.sleep(0.2)
    digitalWrite(_LED_Green, HIGH)
    time.sleep(0.5)
    digitalWrite(_LED_Green, LOW)
    time.sleep(0.2)

# Blinking with red LED
def blink_red():
    print("Red LED blinking")
    digitalWrite(_LED_Red, HIGH)
    delay(1000)
    digitalWrite(_LED_Red, LOW)
    delay(1000)
    digitalWrite(_LED_Red, HIGH)
    delay(1000)
    digitalWrite(_LED_Red, LOW)
    delay(1000)
    digitalWrite(_LED_Red, HIGH)
    delay(1000)
    digitalWrite(_LED_Red, LOW)
    delay(1000)


def onDeviceMethod_red_off(payload):
    print ( "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Direct method called." )
    GPIO.output(_LED_Red, GPIO.LOW)
    time.sleep(0.5)
    GPIO.output(_LED_Red, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(_LED_Red, GPIO.LOW)
    time.sleep(0.5)
    GPIO.output(_LED_Red, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(_LED_Red, GPIO.LOW)
    time.sleep(0.5)
    GPIO.output(_LED_Red, GPIO.HIGH)

def onDeviceMethod_yellow_off(payload):
    GPIO.output(LED_Yellow, GPIO.HIGH)
    time.sleep(int(payload))
    GPIO.output(LED_Yellow, GPIO.LOW)

def onDeviceMethod_green_off(payload):
    GPIO.output(LED_Green, GPIO.HIGH)
    time.sleep(int(payload))
    GPIO.output(LED_Green, GPIO.LOW)

def device_method_callback(method_name, payload, user_context):
    global METHOD_CALLBACKS

    if method_name == "LED_red":
        blink_red()
        #onDeviceMethod_red_off(payload)

    if method_name == "yellow_off":
        onDeviceMethod_yellow_off(payload)

    if method_name ==  "LED_green":
        onDeviceMethod_green_off(payload)

    print ( "\n\nMethod callback called with:\nmethodName = %s\npayload = %s\ncontext = %s" % (method_name, payload, user_context) )
    METHOD_CALLBACKS += 1

    print ( "Total calls confirmed: %d\n" % METHOD_CALLBACKS )
    device_method_return_value = DeviceMethodReturnValue()
    device_method_return_value.response = "{ \"Response\": \"This is the response from the device\" }"
    device_method_return_value.status = 200

    return device_method_return_value


def send_confirmation_callback(message, result, user_context):
    global SEND_CALLBACKS
    print ( "Confirmation[%d] received for message with result = %s" % (user_context, result) )
    map_properties = message.properties()
    print ( "    message_id: %s" % message.message_id )
    print ( "    correlation_id: %s" % message.correlation_id )
    key_value_pair = map_properties.get_internals()
    print ( "    Properties: %s" % key_value_pair )
    SEND_CALLBACKS += 1
    print ( "    Total calls confirmed: %d" % SEND_CALLBACKS )

def get_distance_1():
    start = 0
    stop = 0
    digitalWrite(_LED_Red_0101, HIGH)
    #GPIO.output(_TRIG_1, GPIO.HIGH)
    digitalWrite(_TRIG_1, HIGH)
    time.sleep(0.00001)
    #GPIO.output(_TRIG_1, GPIO.LOW)
    #print(GPIO.input(_TRIG_1))
    digitalWrite(_TRIG_1, LOW)
    temp = time.time()
    while GPIO.input(_ECHO_1) == 0 and time.time() - temp < 4:
        start = time.time()
    while GPIO.input(_ECHO_1) == 1 and time.time() - temp < 4:
        stop = time.time()
    #print("Start time: ",start)
    #print("Stop time: ",stop)
    distance_1 = int((stop-start)*17000)
    if (distance_1/10 < 1):
        digitalWrite(_LED_Blue_0101, HIGH)
        digitalWrite(_LED_Blue_0102, HIGH)
    elif (distance_1/10 < 2 and distance_1/10 >= 1):
        digitalWrite(_LED_Blue_0101, LOW)
        digitalWrite(_LED_Blue_0102, HIGH)
    elif (distance_1/10 >= 2):
        digitalWrite(_LED_Blue_0101, LOW)
        digitalWrite(_LED_Blue_0102, LOW)
    print("Distance_1 = ", distance_1," cm")
    return distance_1

def get_distance_2():
    start = 0
    stop = 0
    time.sleep(0.1)
    digitalWrite(_TRIG_2, HIGH)
    time.sleep(0.00001)
    digitalWrite(_TRIG_2, LOW)
    temp = time.time()
    while GPIO.input(_ECHO_2) == 0 and time.time() - temp < 4:
        start = time.time()
    while GPIO.input(_ECHO_2) == 1 and time.time() - temp < 4:
        stop = time.time()
    distance_2 = int((stop-start)*17000)
    print("Distance_2 = ", distance_2," cm")
    #print("Start time: ",start)
    #print("Stop time: ",stop)
    return distance_2

def get_distance_3():
    start = 0
    stop = 0
    time.sleep(0.1)
    digitalWrite(_TRIG_3, HIGH)
    time.sleep(0.00001)
    digitalWrite(_TRIG_3, LOW)
    temp = time.time()
    while GPIO.input(_ECHO_3) == 0 and time.time() - temp < 4:
        start = time.time()
    while GPIO.input(_ECHO_3) == 1 and time.time() - temp < 4:
        stop = time.time()
    distance_3 = int((stop-start)*17000)
    print("Distance_3 = ", distance_3," cm")
    #print("Start time: ",start)
    #print("Stop time: ",stop)
    return distance_3

def get_distance_4():
    start = 0
    stop = 0
    time.sleep(0.1)
    digitalWrite(_TRIG_4, HIGH)
    time.sleep(0.00001)
    digitalWrite(_TRIG_4, LOW)
    temp = time.time()
    while GPIO.input(_ECHO_4) == 0 and time.time() - temp < 4:
        start = time.time()
    while GPIO.input(_ECHO_4) == 1 and time.time() - temp < 4:
        stop = time.time()
    distance_4 = int((stop-start)*17000)
    print("Distance_4 = ", distance_4," cm")
    #print("Start time: ",start)
    #print("Stop time: ",stop)
    return distance_4

def get_distance_5():
    start = 0
    stop = 0
    time.sleep(0.1)
    digitalWrite(_TRIG_5, HIGH)
    time.sleep(0.00001)
    digitalWrite(_TRIG_5, LOW)
    temp = time.time()
    while GPIO.input(_ECHO_5) == 0 and time.time() - temp < 4:
        start = time.time()
    while GPIO.input(_ECHO_5) == 1 and time.time() - temp < 4:
        stop = time.time()
    distance_5 = int((stop-start)*17000)
    print("Distance_5 = ", distance_5," cm")
    #print("Start time: ",start)
    #print("Stop time: ",stop)
    return distance_5

def get_distance_6():
    start = 0
    stop = 0
    time.sleep(0.1)
    digitalWrite(_TRIG_6, HIGH)
    time.sleep(0.00001)
    digitalWrite(_TRIG_6, LOW)
    temp = time.time()
    while GPIO.input(_ECHO_6) == 0 and time.time() -temp < 4:
        start = time.time()
    while GPIO.input(_ECHO_6) == 1 and time.time() -temp < 4:
        stop = time.time()
    distance_6 = int((stop-start)*17000)
    print("Distance_6 = ", distance_6," cm")
    #print("Start time: ",start)
    #print("Stop time: ",stop)
    return distance_6

def get_distance_7():
    start = 0
    stop = 0
    time.sleep(0.1)
    digitalWrite(_TRIG_7, HIGH)
    time.sleep(0.00001)
    digitalWrite(_TRIG_7, LOW)
    temp = time.time()
    while GPIO.input(_ECHO_7) == 0 and time.time() - temp < 4:
        start = time.time()
    while GPIO.input(_ECHO_7) == 1 and time.time() - temp < 4:
        stop = time.time()
    distance_7 = int((stop-start)*17000)
    print("Distance_7 = ", distance_7," cm")
    #print("Start time: ",start)
    #print("Stop time: ",stop)
    return distance_7

def get_distance_8():
    start = 0
    stop = 0
    time.sleep(0.1)
    digitalWrite(_TRIG_8, HIGH)
    time.sleep(0.00001)
    digitalWrite(_TRIG_8, LOW)
    temp = time.time()
    while GPIO.input(_ECHO_8) == 0 and time.time() - temp < 4:
        start = time.time()
    # add time limitation
    while GPIO.input(_ECHO_8) == 1 and time.time() - temp < 4:
        stop = time.time()
    distance_8 = int((stop-start)*17000)
    print("Distance_8 = ", distance_8," cm")
    #print("Start time: ",start)
    #print("Stop time: ",stop)
    return distance_8

def get_distance_9():
    GPIO.setup(_ECHO_9, GPIO.IN)
    start = 0
    stop = 0
    time.sleep(0.1)
    digitalWrite(_TRIG_9, HIGH)
    time.sleep(0.00001)
    digitalWrite(_TRIG_9, LOW)
    #print("Start time: ",start)
    temp = time.time()
    while GPIO.input(_ECHO_9) == 0 and time.time() - temp < 4:
        start = time.time()
        #print(time.time()-start)
    while GPIO.input(_ECHO_9) == 1 and time.time() - temp < 4:
        stop = time.time()
    distance_9 = int((stop-start)*17000)
    print("Distance_9 = ", distance_9," cm")
    #print("Start time: ",start)
    #print("Stop time: ",stop)
    return distance_9

def get_distance_10():
    GPIO.setup(_ECHO_10, GPIO.IN)
    start = 0
    stop = 0
    time.sleep(0.1)
    digitalWrite(_TRIG_10, HIGH)
    time.sleep(0.00001)
    digitalWrite(_TRIG_10, LOW)
    temp = time.time()
    while GPIO.input(_ECHO_10) == 0 and time.time() - temp < 4:
        start = time.time()
    while GPIO.input(_ECHO_10) == 1 and time.time() - temp < 4:
        stop = time.time()
    distance_10 = int((stop-start)*17000)
    print("Distance_10 = ", distance_10," cm")
    #print("Start time: ",start)
    #print("Stop time: ",stop)
    return distance_10

def get_humidity_1():
    sensor_args = { '11': Adafruit_DHT.DHT11,
                '22': Adafruit_DHT.DHT22,
                '2302': Adafruit_DHT.AM2302 }
    sensor = sensor_args["22"]
    humidity_1, temperature = Adafruit_DHT.read_retry(sensor, 19)
    return humidity_1

def get_temperature_1():
    sensor_args_1 = { '11': Adafruit_DHT.DHT11,
                '22': Adafruit_DHT.DHT22,
                '2302': Adafruit_DHT.AM2302 }
    sensor_1 = sensor_args_1["22"]
    humidity, temperature_1 = Adafruit_DHT.read_retry(sensor_1, 19)
    return temperature_1

def get_gercon_1():
    if (GPIO.input(_Gercon_1) == 1):
        print("Door 1 is open")
    if (GPIO.input(_Gercon_1) == 0):
        print("Door 1 is closed")

def get_gercon_2():
    if (GPIO.input(_Gercon_2) == 1):
        print("Door 2 is open")
    if (GPIO.input(_Gercon_2) == 0):
        print("Door 2 is closed")

def get_gercon_3():
    if (GPIO.input(_Gercon_3) == 1):
        print("Door 3 is open")
    if (GPIO.input(_Gercon_3) == 0):
        print("Door 3 is closed")

def get_gercon_4():
    if (GPIO.input(_Gercon_4) == 1):
        print("Door 4 is open")
    if (GPIO.input(_Gercon_4) == 0):
        print("Door 4 is closed")

def get_gercon_5():
    if (GPIO.input(_Gercon_5) == 1):
        print("Door 5 is open")
    if (GPIO.input(_Gercon_5) == 0):
        print("Door 5 is closed")

def get_gercon_6():
    if (GPIO.input(_Gercon_6) == 1):
        print("Door 6 is open")
    if (GPIO.input(_Gercon_6) == 0):
        print("Door 6 is closed")

def iothub_client_init():
    # prepare iothub client
    client = IoTHubClient(CONNECTION_STRING, PROTOCOL)
    client.set_option("product_info", "RaspberryPi_test_button")
    client.set_option("messageTimeout", MESSAGE_TIMEOUT)
    client.set_message_callback(
        device_method_callback, RECEIVE_CONTEXT)
    #if client.protocol == IoTHubTransportProvider.MQTT or client.protocol == IoTHubTransportProvider.MQTT_WS:
    #    client.set_device_twin_callback(
    #        device_twin_callback, TWIN_CONTEXT)
    client.set_device_method_callback(
        device_method_callback, METHOD_CONTEXT)
    return client

def iothub_client_sample_run():
    try:
        if (check_internet() == True):
            client = iothub_client_init()
            print ("Connecting to IoT Hub")
            if client.protocol == IoTHubTransportProvider.MQTT:
                print ( "IoTHubClient is reporting state" )
                reported_state = "{\"newState\":\"standBy\"}"
                #client.send_reported_state(reported_state, len(reported_state), send_reported_state_callback, SEND_REPORTED_STATE_CONTEXT)
            #telemetry.send_telemetry_data(parse_iot_hub_name(), EVENT_SUCCESS, "IoT hub connection is established")
            #while True:
            global MESSAGE_COUNT,MESSAGE_SWITCH
            if MESSAGE_SWITCH:
                # send a few messages every minute
                print ( "IoTHubClient sending %d messages" % MESSAGE_COUNT )
                #temperature = sensor.read_temperature()
                humidity_1 = get_humidity_1()
                temperature_1 = get_temperature_1()
                distance_1 = get_distance_1()
                distance_2 = get_distance_2()
                distance_3 = get_distance_3()
                distance_4 = get_distance_4()
                distance_5 = get_distance_5()
                distance_6 = get_distance_6()
                distance_7 = get_distance_7()
                distance_8 = get_distance_8()
                #distance_9 = get_distance_9()
                #distance_10 = get_distance_10()

                msg_txt_formatted = MSG_TXT % (
                    distance_1,
                    distance_2,
                    distance_3,
                    distance_4,
                    distance_5,
                    distance_6,
                    distance_7,
                    distance_8,
                    distance_8,
                    distance_8)
                print (msg_txt_formatted)
                message = IoTHubMessage(msg_txt_formatted)
                # optional: assign ids
                message.message_id = "message_%d" % MESSAGE_COUNT
                message.correlation_id = "correlation_%d" % MESSAGE_COUNT
                # optional: assign properties
                prop_map = message.properties()
                prop_map.add("temperatureAlert", "true")

                client.send_event_async(message, send_confirmation_callback, MESSAGE_COUNT)
                print ( "IoTHubClient.send_event_async accepted message [%d] for transmission to IoT Hub." % MESSAGE_COUNT )

                status = client.get_send_status()
                print ( "Send status: %s" % status )
                MESSAGE_COUNT += 1
            time.sleep(2)

    except IoTHubError as iothub_error:
        print ( "Unexpected error %s from IoTHub" % iothub_error )
        telemetry.send_telemetry_data(parse_iot_hub_name(), EVENT_FAILED, "Unexpected error %s from IoTHub" % iothub_error)
        return
    except KeyboardInterrupt:
        print ( "IoTHubClient sample stopped" )

        #print_last_message_time(client)


def read_RFID():
    MIFAREReader = MFRC522.MFRC522()
    RFID_access_list = open("/home/pi/Desktop/RFID_access_list.txt","wr")
    RFID_access_list.read()
    RFID_access_list.close()
    RFID_deny_list = open("/home/pi/Desktop/RFID_deny_list.txt","wr")
    RFID_deny_list.read()
    RFID_deny_list.close()
    print("Read RFID...")
    #GPIO.output(23, GPIO.HIGH)
    # Scan for cards
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
    # If a card is found
    if status == MIFAREReader.MI_OK:
        print "Card detected"
        # Get the UID of the card
        (status,uid) = MIFAREReader.MFRC522_Anticoll()

        # If we have the UID, continue
        if status == MIFAREReader.MI_OK:

            # Print UID
            print "Card read UID: "+str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3])
            # Check access
            if (str(uid[0])=="32" and str(uid[1])=="53" and str(uid[2])=="23" and str(uid[3])=="164"):
                get_gercon_1()
                blink_green()
                iothub_client_sample_run()
            else:
                get_gercon_1()
                blink_red()

            # This is the default key for authentication
            key = [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF]

            # Select the scanned tag
            MIFAREReader.MFRC522_SelectTag(uid)

            # Authenticate
            status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 8, key, uid)

            # Check if authenticated
            if status == MIFAREReader.MI_OK:
                MIFAREReader.MFRC522_Read(8)
                MIFAREReader.MFRC522_StopCrypto1()
            else:
                print "Authentication error"

    #GPIO.output(22, GPIO.LOW)



def read():

    def tobin(data, width=8):
        data_str = bin(data & (2**width-1))[2:].zfill(width)
        return data_str

    # shiftr = CD4021(clock=11, latch=9, data=4)
    shiftr = SN74LS165(clock=23, latch=26, data=21, clock_enable=18) #21->13 23->15
    try:
        # b1 = shiftr.read_one_byte()
        # print(format(b1, '#010b'))
        # bytes = [ shiftr.read_one_byte() ]
        bytes = [ shiftr.read_shift_regs() ]
        print('   '.join([tobin(b, 8) for b in bytes]))
        print('   '.join(["%8x" % b for b in bytes]))
        # Sleep at least .0001 between reads
        time.sleep(1)
        bashCommand = "raspi-gpio set 11 a0"
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        bashCommand = "raspi-gpio set 9 a0"
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
    except KeyboardInterrupt:
        GPIO.cleanup()


# Infinity cycle
try:
    while continue_reading:
        print("000000")
        #get_gercon_1()
        #get_gercon_2()
        #get_gercon_3()
        #get_gercon_4()
        #get_gercon_5()
        #get_gercon_6()
        #blink_green()
        #blink_red()
        get_distance_1()
        time.sleep(1)
        #get_distance_2()
        #time.sleep(1)
        #get_distance_3()
        #time.sleep(1)
        #get_distance_4()
        #time.sleep(1)
        #get_distance_5()
        #time.sleep(1)
        #get_distance_6()
        #time.sleep(1)
        #get_distance_7()
        #time.sleep(1)
        #get_distance_8()
        #time.sleep(1)
        #get_distance_9()
        #time.sleep(1)
        #get_distance_10()
        #iothub_client_sample_run()
        time.sleep(1)
        #iothub_client_init()
        #read()
        #read_RFID()

except KeyboardInterrupt:
    print('KeyboardInterrupt')
    end_read()