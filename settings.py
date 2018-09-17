DEBUG = False

DEFAULT_NUMBER_OF_SENSORS = 10
DEFAULT_IS_INIT_HARDWARE = True
DEFAULT_PULSE_LENGTH = 0.00001      # sensor trigger pulse width
DEFAULT_DIST_SENSOR_TIMEOUT = 0.01  # timeout to wait for sensor data. error if exceeded

# levels of distance (HIGH_DISTANCE_LIMIT -> LEVEL_1_DISTANCE -> LEVEL_2_DISTANCE -> LOW_DISTANCE_LIMIT)
LOW_DISTANCE_LIMIT = 30
HIGH_DISTANCE_LIMIT = 250
LEVEL_1_DISTANCE = 100
LEVEL_2_DISTANCE = 50

SCANNING_INTERVAL = 1               # timeout between all sensors scans
INTER_SENSOR_INTERVAL = 0.2         # timeout between sensors polling - to reduce noise
DISPLAY_UPDATE_INTERVAL = 1                #timeout between display updates

# INDICATION line settings
PIN_CH_A = 29  # 5
PIN_CH_B = 7  # 4

# SR-04 SENSORS Controller config
SENSOR_DEFAULT_CONFIG = {
    'PIN_ADDR_0': 15,
    'PIN_ADDR_1': 16,
    'PIN_ADDR_2': 18,
    'PIN_ADDR_3': 22,
    'PIN_TRIG': 11,
    'PIN_ECHO': 13
}


# SHIFT_595 DIAG Controller config
SHIFT_595_STATUS__DEFAULT_CONFIG = {
    'PIN_SER': 40,
    'PIN_RCLK': 38,
    'PIN_SRCLK': 37,
}

# SHIFT_595 STATUS Controller config
SHIFT_595_ERROR__DEFAULT_CONFIG = {
    'PIN_SER': 31,
    'PIN_RCLK': 33,
    'PIN_SRCLK': 35,
}

# 74hc595 settings:

# status panel
PIN_SHIFT_STATUS_SER = 40
PIN_SHIFT_STATUS_RCLK = 38
PIN_SHIFT_STATUS_SRCLK = 37

# error panel
PIN_SHIFT_ERROR_SER = 31
PIN_SHIFT_ERROR_RCLK = 33
PIN_SHIFT_ERROR_SRCLK = 35

IOT_HUB_CONN_STRING = 'HostName=uralchem-iot-hub.azure-devices.net;DeviceId=RaspberryPi_test_button;SharedAccessKey' \
                      '=QqLFpZw7rtElA87DZ/mx2dJ1KaCchA/wTFLgU1+EEI8= '
IOT_HUB_MSG_TXT = "{\"deviceId\": \"RaspberryPi_test_button""\",\"distance_1\": %f,\"distance_2\": %f,\"distance_3\": " \
                  "%f,\"distance_4\": %f,\"distance_5\": %f,\"distance_6\": %f,\"distance_7\": %f,\"distance_8\": %f," \
                  "\"distance_9\": %f,\"distance_10\": %f} "

