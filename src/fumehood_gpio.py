import RPi.GPIO as gpio

class FumeHoodGPIO:

	# v0 (No PCB)
	# Inputs
	PIN_LOWER_LIMIT = 36
	PIN_UPPER_LIMIT = 32
	PIN_MANUAL_LOWER = 38
	PIN_MANUAL_OVERRIDE = 40

	# Outputs
	PIN_LED_R = 29
	PIN_LED_G = 31
	PIN_LED_B = 33
	PIN_MOTOR_UP = 37
	PIN_MOTOR_DOWN = 35

	"""
	# v4 (PCB v4.9)
	# Inputs
	PIN_LOWER_LIMIT = 24
	PIN_UPPER_LIMIT = 26
	PIN_MANUAL_LOWER = 38
	PIN_MANUAL_OVERRIDE = 40

	# Outputs
	PIN_LED_R = 12
	PIN_LED_G = 8
	PIN_LED_B = 10
	PIN_MOTOR_UP = 16
	PIN_MOTOR_DOWN = 22
	"""

	"""
	# v4.10 (PCB v4.10)
	# Inputs
	PIN_LOWER_LIMIT = 32
	PIN_UPPER_LIMIT = 36
	PIN_MANUAL_LOWER = 38
	PIN_MANUAL_OVERRIDE = 40

	# Outputs
	PIN_LED_R = 8
	PIN_LED_G = 10
	PIN_LED_B = 12
	PIN_MOTOR_UP = 18
	PIN_MOTOR_DOWN = 22
	"""

	@staticmethod
	def Get(pin):
		return bool(gpio.input(pin))

	@staticmethod
	def Set(pin, state):
		gpio.output(pin, state)

	@staticmethod
	def Clear():
		"""Set all outputs to default states (which are all low)"""
		gpio.output(FumeHoodGPIO.PIN_LED_R, gpio.LOW)
		gpio.output(FumeHoodGPIO.PIN_LED_G, gpio.LOW)
		gpio.output(FumeHoodGPIO.PIN_LED_B, gpio.LOW)
		gpio.output(FumeHoodGPIO.PIN_MOTOR_UP, gpio.LOW)
		gpio.output(FumeHoodGPIO.PIN_MOTOR_DOWN, gpio.LOW)

	@staticmethod
	def Init():
		# Set up GPIO configuration
		gpio.setmode(gpio.BOARD)

		# Kill warnings
		gpio.setwarnings(False)

		# Set up GPIO pin inputs/outputs
		gpio.setup(FumeHoodGPIO.PIN_LOWER_LIMIT, gpio.IN, pull_up_down=gpio.PUD_DOWN)
		gpio.setup(FumeHoodGPIO.PIN_UPPER_LIMIT, gpio.IN, pull_up_down=gpio.PUD_DOWN)
		gpio.setup(FumeHoodGPIO.PIN_MANUAL_LOWER, gpio.IN, pull_up_down=gpio.PUD_DOWN)
		gpio.setup(FumeHoodGPIO.PIN_MANUAL_OVERRIDE, gpio.IN, pull_up_down=gpio.PUD_DOWN)
		gpio.setup(FumeHoodGPIO.PIN_LED_R, gpio.OUT)
		gpio.setup(FumeHoodGPIO.PIN_LED_G, gpio.OUT)
		gpio.setup(FumeHoodGPIO.PIN_LED_B, gpio.OUT)
		gpio.setup(FumeHoodGPIO.PIN_MOTOR_UP, gpio.OUT)
		gpio.setup(FumeHoodGPIO.PIN_MOTOR_DOWN, gpio.OUT)

		# Set all outputs to default states
		# These are all low so initialization is safe
		FumeHoodGPIO.Clear()
	
