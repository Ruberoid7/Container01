import time

import RPi.GPIO as GPIO

from .dist_sensor_states import DistSensorNormalState

from utils import *

def make_mux(**kwargs):
    return MUX(**kwargs)


def make_dist_sensor(**kwargs):
    return DistSensor(**kwargs)


class DistSensor(object):
    # levels of distance (HIGH_DISTANCE_LIMIT -> LEVEL_1_DISTANCE -> LEVEL_2_DISTANCE -> LOW_DISTANCE_LIMIT)
    _LEVEL_1_DISTANCE, _LEVEL_2_DISTANCE = settings.LEVEL_1_DISTANCE, settings.LEVEL_2_DISTANCE

    def __init__(self, mux, number, low_limit=settings.LOW_DISTANCE_LIMIT, high_limit=settings.HIGH_DISTANCE_LIMIT):
        self._number, self._mux = number, mux
        self.LOW_DISTANCE_LIMIT, self.HIGH_DISTANCE_LIMIT = low_limit, high_limit

        # measured distance to average calc
        self._last_distance = self._current_distance = 0

        # status state
        self._current_state = self._prev_state = DistSensorNormalState.levels[0]

        self._errors_count_seq = 0

    def __repr__(self):
        return 'Sensor({}) : {} ({})'.format(self._number, self.level, self.distance)

    def __str__(self):
        dist_str = str(self.distance)
        if self.distance > settings.HIGH_DISTANCE_LIMIT:
            dist_str = 'TO HIGH'
        elif self.distance < settings.LOW_DISTANCE_LIMIT:
            dist_str = 'TO LOW'
        return ' Sensor {} : {}({})'.format(self._number + 1, str(self._current_state),  dist_str)

    # def __call__(self, *args, **kwargs):

    @property
    def distance(self):
        return self._current_distance

    @property
    def level(self):
        if self._current_state.is_error():
            return self._prev_state.level
        else:
            return self._current_state.level

    @property
    def is_error(self):
        return self._current_state.is_error()

    def _select_sensor(self):
        self._mux.select_sensor(self._number)
        return self

    def _send_trigger(self):
        self._mux.send_trigger()
        return self

    def _wait_for_echo(self, timeout=settings.DEFAULT_DIST_SENSOR_TIMEOUT):
        return self._mux.wait_for_echo(timeout)

    def _select_and_measure_cycle(self):
        return self._select_sensor()._send_trigger()._wait_for_echo()

    def get_distance(self):
        distance = self._current_distance

        error, start, stop = self._select_and_measure_cycle()

        if error == 0:
            distance = int((stop - start) * 17000)
            self._last_distance, self._current_distance = self._current_distance, distance

            if not (self.LOW_DISTANCE_LIMIT <= distance <= self.HIGH_DISTANCE_LIMIT):
                error = 2

        # print("Error: ", error)
        # print("Distance = ", distance, " cm")
        return error, distance

    def _determine_level(self, distance):
        # levels of distance (HIGH_DISTANCE_LIMIT -> LEVEL_1_DISTANCE -> LEVEL_2_DISTANCE -> LOW_DISTANCE_LIMIT)
        if distance < self._LEVEL_1_DISTANCE:
            if distance > self._LEVEL_2_DISTANCE:
                return 1
            else:
                return 2
        return 0

    def measure_distance(self):
        error, distance = self.get_distance()

        # change state - control transition
        if error == 0:
            new_level = self._determine_level(distance)
            self.on_event('set_level', new_level)
        else:
            self.on_event('device_error')

    # State Machine switch
    def on_event(self, event, param=None):
        new_state = self._current_state.on_event(event, param)

        if new_state != self._current_state:
            self._prev_state, self._current_state = self._current_state, new_state

            # !!!placeholder - change indication and send message here!!!
            # self._mux.


# Container for Sensors and Hardware controller
class MUX(object):
    def __init__(self,
                 *,
                 selector_config=settings.SENSOR_DEFAULT_CONFIG,
                 number_of_sensors=settings.DEFAULT_NUMBER_OF_SENSORS,
                 is_init_hardware=settings.DEFAULT_IS_INIT_HARDWARE):
        # self._dist_sensors = list()

        # parse and check config
        selector_config['PIN_ADDR_0'] = get_config_value('PIN_ADDR_0', selector_config)
        selector_config['PIN_ADDR_1'] = get_config_value('PIN_ADDR_1', selector_config)
        selector_config['PIN_ADDR_2'] = get_config_value('PIN_ADDR_2', selector_config)
        selector_config['PIN_ADDR_3'] = get_config_value('PIN_ADDR_3', selector_config)

        selector_config['PIN_TRIG'] = get_config_value('PIN_TRIG', selector_config)
        selector_config['PIN_ECHO'] = get_config_value('PIN_ECHO', selector_config)

        self._selector_config = selector_config
        self.last_scan_time = 0.0

        is_init_hardware and self.init_ports(selector_config)

        # create list of sensors
        self._dist_sensors = [DistSensor(self, sensor_num) for sensor_num in range(number_of_sensors)]

    def __len__(self):
        return len(self._dist_sensors)

    def __getitem__(self, num):
        return self._dist_sensors[num]

    def __iter__(self):
        return iter(self._dist_sensors)

    def __repr__(self):
        repr_str = ''
        for sensor in self:
            repr_str += repr(sensor)
        return repr_str

    def __str__(self):
        repr_str = ''
        for sensor in self:
            repr_str += str(sensor)
        return repr_str

    @staticmethod
    def init_ports(selector_config=settings.SENSOR_DEFAULT_CONFIG):
        """ INIT hardware ports """

        if settings.DEBUG:
            print('Config: ', selector_config)

        GPIO.setup(selector_config['PIN_ADDR_0'], GPIO.OUT)
        GPIO.setup(selector_config['PIN_ADDR_1'], GPIO.OUT)
        GPIO.setup(selector_config['PIN_ADDR_2'], GPIO.OUT)
        GPIO.setup(selector_config['PIN_ADDR_3'], GPIO.OUT)

        GPIO.setup(selector_config['PIN_TRIG'], GPIO.OUT)
        GPIO.setup(selector_config['PIN_ECHO'], GPIO.IN)

    def select_sensor(self, num):
        # num = num - 1
        GPIO.output(self._selector_config['PIN_ADDR_3'], (num & (0x01 << 3)) >> 3)
        GPIO.output(self._selector_config['PIN_ADDR_2'], (num & (0x01 << 2)) >> 2)
        GPIO.output(self._selector_config['PIN_ADDR_1'], (num & (0x01 << 1)) >> 1)
        GPIO.output(self._selector_config['PIN_ADDR_0'], (num & (0x01 << 0)) >> 0)

        # print('_PIN_ADDR_3', (num & (0x01 << 3 )) >> 3)
        # print('_PIN_ADDR_2', (num & (0x01 << 2 )) >> 2)
        # print('_PIN_ADDR_1', (num & (0x01 << 1 )) >> 1)
        # print('_PIN_ADDR_0', (num & (0x01 << 0 )) >> 0)
        # print("_________________")

    def send_trigger(self, pulse_length=settings.DEFAULT_PULSE_LENGTH):
        pin_trig = self._selector_config['PIN_TRIG']
        GPIO.output(pin_trig, GPIO.HIGH)
        time.sleep(pulse_length)
        GPIO.output(pin_trig, GPIO.LOW)

    def wait_for_echo(self, timeout=settings.DEFAULT_DIST_SENSOR_TIMEOUT):
        start = stop = error = 0.0
        pin_echo = self._selector_config['PIN_ECHO']

        start_moment = time.time()

        while GPIO.input(pin_echo) == 0:
            start = time.time()
            if start - start_moment >= timeout:
                error = 1
                break
        while GPIO.input(pin_echo) == 1:
            stop = time.time()
            if stop - start_moment >= timeout:
                error = 1
                break
        return error, start, stop

    def measure_distance_on_sensor_num(self, num):
        self[num].measure_distance()

    def measure_distance_on_sensor(self, sensor):
        sensor.measure_distance()

    def measure_all_sensors(self, timeout=0.1):
        # do not scan to often
        if time.time() - self.last_scan_time < settings.SCANNING_INTERVAL:
            return
        for sensor in self:
            self.measure_distance_on_sensor(sensor)
            time.sleep(timeout)
