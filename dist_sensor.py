import time

import RPi.GPIO as GPIO
from dist_sensor_states import DistSensorErrorState, DistSensorNormalState

_DEBUG = False

_DEFAULT_NUMBER_OF_SENSORS = 10
_DEFAULT_IS_INIT_HARDWARE = True
_DEFAULT_PULSE_LENGTH = 0.00001
_LOW_DISTANCE_LIMIT = 10
_HIGH_DISTANCE_LIMIT = 250

#PINS config
_DEFAULT_CONFIG = {
    'PIN_ADDR_0': 15,
    'PIN_ADDR_1': 16,
    'PIN_ADDR_2': 18,
    'PIN_ADDR_3': 22,
    'PIN_TRIG': 11,
    'PIN_ECHO': 13
    }

#Container for Sensors and Hardware controller                      
class MUX(object):
    def __init(self, selector_config=_DEFAULT_CONFIG, number_of_sensors = _DEFAULT_NUMBER_OF_SENSORS, is_init_hardware=_DEFAULT_IS_INIT_HARDWARE):
        #self._dist_sensors = list()

        #parse and check config
        selector_config['PIN_ADDR_0'] = get_config_value('PIN_ADDR_0', selector_config)
        selector_config['PIN_ADDR_1'] = get_config_value('PIN_ADDR_1', selector_config)
        selector_config['PIN_ADDR_2'] = get_config_value('PIN_ADDR_2', selector_config)            
        selector_config['PIN_ADDR_3'] = get_config_value('PIN_ADDR_3', selector_config)
        
        selector_config['PIN_TRIG'] = get_config_value('PIN_TRIG', selector_config)
        selector_config['PIN_ECHO'] = get_config_value('PIN_ECHO', selector_config)

        self._selector_config = selector_config

        is_init_hardware or self.init_ports(selector_config)

         #create list of sensors
        self._dist_sensors = [DistSensor(self, sensor_num) for sensor_num in range(number_of_sensors)]

    def __len__(self):
        return len(self._dist_sensors)
    
    def __get_item__(self, num):
        return self._dist_sensors[num]

    def __iter__(self):
        return iter(self._dist_sensors)

    def __repr__(self):
        repr_str = ''
        for sensor in self:
            repr_str += repr(sensor)
        return repr_str
            

    def init_ports(selector_config=_DEFAULT_CONFIG):
        """
        INIT hardware ports
        """
        if _DEBUG:
            print('Config: ', selector_config)
            
        GPIO.setup(selector_config['PIN_ADDR_0'], GPIO.OUT)
        GPIO.setup(selector_config['PIN_ADDR_1'], GPIO.OUT)
        GPIO.setup(selector_config['PIN_ADDR_2'], GPIO.OUT)
        GPIO.setup(selector_config['PIN_ADDR_3'], GPIO.OUT)
        
        GPIO.setup(selector_config['PIN_TRIG'], GPIO.OUT)
        GPIO.setup(selector_config['PIN_ECHO'], GPIO.IN)
        
            
    def get_config_value(key, selector_config=_DEFAULT_CONFIG):
        #ToDo: rewrite - test will fail if 0 or None was passed...
        found = selector_config.get(key)
        if found:
            found = int(found)
        else:
            found = int(_DEFAULT_CONFIG[key])
        return found

    def select_sensor(self, addr):
        #addr = addr - 1
        GPIO.output(self._selector_config['PIN_ADDR_3'], (addr & (0x01 << 3 )) >> 3)
        GPIO.output(self._selector_config['PIN_ADDR_2'], (addr & (0x01 << 2 )) >> 2)
        GPIO.output(self._selector_config['PIN_ADDR_1'], (addr & (0x01 << 1 )) >> 1)
        GPIO.output(self._selector_config['PIN_ADDR_0'], (addr & (0x01 << 0 )) >> 0)

        #print(_PIN_ADDR_3, (addr & (0x01 << 3 )) >> 3)
        #print(_PIN_ADDR_2, (addr & (0x01 << 2 )) >> 2)
        #print(_PIN_ADDR_1, (addr & (0x01 << 1 )) >> 1)
        #print(_PIN_ADDR_0, (addr & (0x01 << 0 )) >> 0)
        #print("_________________")

    def send_trigger(self, pulse_length = _DEFAULT_PULSE_LENGTH):
        pin_trig = self._selector_config['PIN_TRIG']
        GPIO.output(pin_trig, GPIO.HIGH)
        time.sleep(pulse_length)
        GPIO.output(pin_trig, GPIO.LOW)

    def wait_for_echo(self, timeout = 4):
        start = 0
        stop = 0
        error = 0
        pin_echo = self._selector_config['PIN_ECHO']

        startMoment = time.time()
        
        while GPIO.input(pin_echo) == 0:
            start = time.time()
            if start - startMoment >= timeout:
                error = 1
                break
        while GPIO.input(pin_echo) == 1:
            stop = time.time()
            if stop - startMoment >= timeout:
                error = 1
                break
            
        return error,start,stop
    
    def measure_distance_on_sensor_num(self, num):
        self[num].measure_distance()

    def measure_distance_on_sensor(self, sensor):
        sensor.measure_distance()
    
    def measure_all_sensors(self):
        for sensor in self:
            self.measure_distance_on_sensor(sensor)

def make_mux(**kwargs):
    return MUX(**kwargs)
    
        
class DistSensor(object):
    #levels of distance (_HIGH_DISTANCE_LIMIT -> LEVEL_1_DISTANCE -> LEVEL_2_DISTANCE -> _LOW_DISTANCE_LIMIT)
    _LEVEL_1_DISTANCE = 100
    _LEVEL_2_DISTANCE = 50    

    def __init__(self, mux, number, lowlimit=_LOW_DISTANCE_LIMIT, highlimit=_HIGH_DISTANCE_LIMIT):
        self._number = number
        self._mux = mux
        self._LOW_DISTANCE_LIMIT = lowlimit
        self._HIGH_DISTANCE_LIMIT = highlimit

        #measured distance to average calc
        self._last_distance = self._current_distance = 0
        self._last_level = self._current_level = 0
        
        #status state
        self._current_state = self._prev_state = DistSensorNormalState(0)
        
        self._errors_count_seq = 0

    def __repr__(self):
        return self.__class__.__name__ + " # " + str(self._number)

    @property
    def last_distance(self):
        return self._last_distance

    def last_level(self):
        return self._last_level
    

    def _select_sensor(self):
        self._mux.select_sensor(self._number)
        return self

    def _send_trigger(self):
        self._mux.send_trigger()
        return self

    def _wait_for_echo(self, timeout=4):
        return self._mux.wait_for_echo(timeout)        
        
    def get_distance(self):
        distance = self._current_distance
        
        self._select_sensor()
        self._send_trigger()
        error, start, stop = self._wait_for_echo()

        if (error < 1) and ((distance < self._LOW_DISTANCE_LIMIT) or (distance > self._HIGH__DISTANCE_LIMIT)):
            error = 2

        if (error == 0):
            distance = int((stop - start) * 17000)
            self._last_distance = self._current_distance
            self._current_distance = distance
            
        #print("Error: ", error)
        #print("Distance = ", distance," cm")
        return error, distance

    def _determine_level(distance):
        #levels of distance (_HIGH_DISTANCE_LIMIT -> LEVEL_1_DISTANCE -> LEVEL_2_DISTANCE -> _LOW_DISTANCE_LIMIT)
        if (distance < self._LEVEL_1_DISTANCE):
            if (distance > self_LEVEL_2_DISTANCE ):
                return 1
            else:
                return 2
        return 0

    def measure_distance(self):
        error, distance = self.get_distance()

        #change state - control transition
        if (error == 0):
            level = self._determine_level(distance)
            self.on_event('set_level', level)
        else:
            self.on_event('device_error')

    #State Machine switch
    def on_event(self, event, param = None):
        new_state = self._current_state.on_event(event, param)
        
        if (new_state != self.current_state):
            self._prev_state = self._current_state
            self._current_state = new_state
            #!!!placeholder - change indication and send message here!!!
            #self._mux.

            

        

        
