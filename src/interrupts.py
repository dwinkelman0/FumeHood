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
	EVENT_PUSHER_LEAVES_TOP = 10

	# Table
	EVENT_TABLE = {
		0: "EVENT_NONE",
		1: "EVENT_ACTIVITY",
		2: "EVENT_OBSTRUCTION",
		3: "EVENT_ACTIVITY_TIMEOUT",
		4: "EVENT_MANUAL_OVERRIDE",
		5: "EVENT_OVERRIDE_TIMEOUT",
		6: "EVENT_MANUAL_CLOSE",
		7: "EVENT_SASH_OPENED",
		8: "EVENT_SASH_CLOSED",
		9: "EVENT_PUSHER_REACHES_TOP",
		10: "EVENT_PUSHER_LEAVES_TOP"
	}

	def __init__(self):
		super(Interrupt, self).__init__()
		self.event = Interrupt.EVENT_NONE

	def Send(self, code):
		with self:
			print("Interrupt {:}".format(self.EVENT_TABLE[code]))
			self.event = code
			self.notify_all()

	def Read(self):
		output = self.event
		self.event = Interrupt.EVENT_NONE
		return output

	def TriggeredSend(self, pin, event_rising, event_falling):
		"""Callback for edge detection"""
		# Rising
		if event_rising is not None and fhgpio.Get(pin):
			self.Send(event_rising)
			return

		# Falling
		if event_falling is not None and not fhgpio.Get(pin):
			self.Send(event_falling)
			return

	def InitTriggers(self):
		"""Attach rising/falling edge triggers to GPIO inputs"""
		gpio.add_event_detect(fhgpio.PIN_LOWER_LIMIT, gpio.BOTH,
			lambda _pin: self.TriggeredSend(
				_pin,
				Interrupt.EVENT_SASH_CLOSED,
				Interrupt.EVENT_SASH_OPENED))
		gpio.add_event_detect(fhgpio.PIN_UPPER_LIMIT, gpio.BOTH,
			lambda _pin: self.TriggeredSend(
				_pin, 
				Interrupt.EVENT_PUSHER_REACHES_TOP,
				Interrupt.EVENT_PUSHER_LEAVES_TOP))
		gpio.add_event_detect(fhgpio.PIN_MANUAL_LOWER, gpio.BOTH,
			lambda _pin: self.TriggeredSend(
				_pin,
				Interrupt.EVENT_MANUAL_CLOSE,
				None))
		gpio.add_event_detect(fhgpio.PIN_MANUAL_OVERRIDE, gpio.BOTH,
			lambda _pin: self.TriggeredSend(
				_pin,
				Interrupt.EVENT_MANUAL_OVERRIDE,
				None))
