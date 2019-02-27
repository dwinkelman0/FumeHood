from fumehood_gpio import FumeHoodGPIO as fhgpio
from fumehood_gpio import gpio

import threading

class Interrupt(threading.Condition):

	# Events
	EVENT_NONE = 0
	EVENT_ACTIVITY = 1
	EVENT_OBSTRUCTION = 2
	EVENT_ACTIVITY_TIMEOUT = 3
	EVENT_MANUAL_OVERRIDE = 4
	EVENT_OVERRIDE_TIMEOUT = 5
	EVENT_MANUAL_CLOSE = 6
	EVENT_SASH_OPENED = 7
	EVENT_SASH_CLOSED = 8
	EVENT_PUSHER_REACHES_TOP = 9

	def __init__(self):
		super(Interrupt, self).__init__()
		self.event = Interrupt.EVENT_NONE

	def Send(self, code):
		with self:
			self.event = code
			self.notify_all()

	def Read(self):
		output = self.event
		self.event = Interrupt.EVENT_NONE
		return output

	def TriggeredSend(pin, event_rising, event_falling):
		print(pin)
		"""Callback for edge detection"""
		# Rising
		if event_rising is not None and fhgpio.Read(pin):
			self.Send(event_rising)
			return

		# Falling
		if event_falling is not None and not fhgpio.Read(pin):
			self.Send(event_falling)
			return

	def InitTriggers(self):
		"""Attach rising/falling edge triggers to GPIO inputs"""
		gpio.add_event_detect(fhgpio.PIN_LOWER_LIMIT, gpio.BOTH,
			lambda pin: self.TriggeredSend(
				pin=pin,
				event_rising=Interrupt.EVENT_SASH_CLOSED,
				event_falling=Interrupt.EVENT_SASH_OPENED))
		gpio.add_event_detect(fhgpio.PIN_UPPER_LIMIT, gpio.BOTH,
			lambda pin: self.TriggeredSend(
				pin=pin, 
				event_rising=Interrupt.EVENT_PUSHER_REACHES_TOP,
				event_falling=None))
		gpio.add_event_detect(fhgpio.PIN_MANUAL_LOWER, gpio.BOTH,
			lambda pin: self.TriggeredSend(
				pin=pin,
				event_rising=Interrupt.EVENT_MANUAL_LOWER,
				event_falling=None))
		gpio.add_event_detect(fhgpio.PIN_MANUAL_OVERRIDE, gpio.BOTH,
			lambda pin: self.TriggeredSend(
				pin=pin,
				event_rising=Interrupt.EVENT_MANUAL_OVERRIDE,
				event_falling=None))

