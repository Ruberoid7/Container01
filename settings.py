DEBUG = False

DEFAULT_NUMBER_OF_SENSORS = 10
DEFAULT_IS_INIT_HARDWARE = True
DEFAULT_PULSE_LENGTH = 0.00001
LOW_DISTANCE_LIMIT = 10
HIGH_DISTANCE_LIMIT = 250

#PINS config
DEFAULT_CONFIG = {
    'PIN_ADDR_0': 15,
    'PIN_ADDR_1': 16,
    'PIN_ADDR_2': 18,
    'PIN_ADDR_3': 22,
    'PIN_TRIG': 11,
    'PIN_ECHO': 13
    }

IOT_HUB_CONN_STRING = 'HostName=uralchem-iot-hub.azure-devices.net;DeviceId=RaspberryPi_test_button;SharedAccessKey=QqLFpZw7rtElA87DZ/mx2dJ1KaCchA/wTFLgU1+EEI8='
IOT_HUB_MSG_TXT = "{\"deviceId\": \"RaspberryPi_test_button""\",\"distance_1\": %f,\"distance_2\": %f,\"distance_3\": %f,\"distance_4\": %f,\"distance_5\": %f,\"distance_6\": %f,\"distance_7\": %f,\"distance_8\": %f,\"distance_9\": %f,\"distance_10\": %f}"

PIN_SHIFT_STATUS_SER = 40
PIN_SHIFT_STATUS_RCLK = 38
PIN_SHIFT_STATUS_SRCLK = 37

PIN_SHIFT_ERROR_SER = 31
PIN_SHIFT_ERROR_RCLK = 33
PIN_SHIFT_ERROR_SRCLK = 35
