# http://python-3-patterns-idioms-test.readthedocs.io/en/latest/StateMachine.html

# sys.path += ['../stateMachine', '../mouse']
import time
import signal

import RPi.GPIO as GPIO

import settings
import led_control
import dist_sensor

GPIO.setmode(GPIO.BOARD)

# init indication line controller
GPIO.setup(settings.PIN_CH_A, GPIO.OUT)
GPIO.setup(settings.PIN_CH_B, GPIO.OUT)

def set_ind_line(mode=GPIO.LOW):
    GPIO.output(settings.PIN_CH_A, mode)
    GPIO.output(settings.PIN_CH_A, mode)

set_ind_line()

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

status_leds_controller = led_control.make_led_panel(controller_config=settings.SHIFT_595_STATUS__DEFAULT_CONFIG,
                                                    led_id_convert_func=led_control.status_led_id_convert)

errors_leds_controller = led_control.make_led_panel(controller_config=settings.SHIFT_595_ERROR__DEFAULT_CONFIG,
                                                    led_id_convert_func=led_control.default_led_id_convert)
# led_control.diag_leds()

mux = dist_sensor.make_mux()


continue_reading = True
_levels_to_led_states_map = [led_control.HIGH, led_control.BLINK, led_control.LOW]

try:
    while continue_reading:
        mux.measure_all_sensors(timeout=settings.INTER_SENSOR_INTERVAL)
        # print(mux)
        print('='*100)

        # process display
        for sensor, status_led, error_led in zip(mux, status_leds_controller, errors_leds_controller):
            print('%-35s%-35s%s' % (sensor, status_led, error_led))
            if sensor.is_error:
                error_led.state = led_control.HIGH
                status_led.state = led_control.LOW
            else:
                error_led.state = led_control.LOW
                status_led.state = _levels_to_led_states_map[sensor.level]
            time.sleep(0.1)

        time.sleep(settings.DISPLAY_UPDATE_INTERVAL)

except KeyboardInterrupt:
    print('KeyboardInterrupt')
    end_read()

GPIO.cleanup()
