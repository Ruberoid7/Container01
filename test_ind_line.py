import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)

_PIN_CH_A = 29  # 5
_PIN_CH_B = 7  # 4

# GPIO.setmode(GPIO.BCM)
GPIO.setmode(GPIO.BOARD)

GPIO.setup(_PIN_CH_A, GPIO.OUT)
GPIO.setup(_PIN_CH_B, GPIO.OUT)

# GPIO.output(_PIN_CH_A, GPIO.HIGH)
GPIO.output(_PIN_CH_A, GPIO.LOW)

# GPIO.output(_PIN_CH_B, GPIO.HIGH)
GPIO.output(_PIN_CH_B, GPIO.LOW)
