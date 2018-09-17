import time
import logging
import settings
import shift_595
from shift_595 import HIGH, ALL, LOW
from . led_utils import default_led_id_convert

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.debug('This is a log message.')

BLINK = 2   # led mode addendum for shift_595 modes list


def make_led_panel(**kwargs):
    return LedControlPanel(**kwargs)


def make_led_control(**kwargs):
    return LedControl(**kwargs)


class LedControl(object):
    """
    Control single led
    """

    def __init__(self, panel, uid, state=LOW):
        # super().__init__()
        self._panel, self._uid = panel, uid
        self._last_state = self._current_state = state

    def __repr__(self):
        return self.__class__.__name__ + " # " + str(self.uid) + ' : ' + repr(self.state) + ' | '

    @property
    def state(self):
        return self._current_state

    @state.setter
    def state(self, new_state):
        if new_state not in (HIGH, LOW, BLINK):
            raise ValueError('Invalid state value')
        if new_state != self._current_state:
            self._last_state, self._current_state = self._current_state, new_state
            self.activate_state()

    def activate_state(self):
        self._panel.activate_state_on_led(self)

    @property
    def last_state(self):
        return self._last_state

    @property
    def uid(self):
        return self._uid


class LedControlPanel(object):
    """
    Control led_panel
    """

    def __init__(self, *, controller_config=None, controller=None, number_of_leds=settings.DEFAULT_NUMBER_OF_SENSORS,
                 led_id_convert_func=default_led_id_convert):
        # create list of leds
        self._leds = [LedControl(self, led_num) for led_num in range(number_of_leds)]
        self._id_convert_func = led_id_convert_func

        # create 595 controller object
        if controller:
            self._controller = controller
        elif controller_config:
            self._controller = shift_595.SN74x595(
                ser_pin=controller_config.get('PIN_SER'),
                rclk_pin=controller_config.get('PIN_RCLK'),
                srclk_pin=controller_config.get('PIN_SRCLK')
            )
        else:
            raise(ValueError('controller or controller_config must be specified'))

        self.set_state_for_all(LOW)

    def __repr__(self):
        repr_str = ''
        for led in self:
            repr_str += repr(led)
        return repr_str

    def __len__(self):
        return len(self._leds)

    def __getitem__(self, num):
        return self._leds[num]

    def __setitem__(self, num, value):
        self._leds[num].state = value

    def __iter__(self):
        return iter(self._leds)

    def _check_led_num(self, led_num):
        if led_num >= len(self) or led_num < 0:
            raise ValueError('Invalid led number')

    def activate_state_on_led_num(self, led_num):
        self.activate_state_on_led(self[led_num])

    def activate_state_on_led(self, led):
        led_addr = self._id_convert_func(led.uid)             # get addr for led
        print('Flash LED address: ', led_addr, ' for led-id: ', led.uid)
        self._controller.digitalWrite(led_addr, led.state)    # actuate state

    def set_state_for_all(self, new_state=LOW):
        for led in self:
            led.state = new_state
            self.activate_state_on_led(led)

    def test_leds(self, timeout=3):
        self.set_state_for_all(new_state=HIGH)
        time.sleep(timeout)
        self.set_state_for_all(new_state=LOW)

