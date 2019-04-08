from camera import Camera
from fumehood_gpio import FumeHoodGPIO as fhgpio
from interrupts import Interrupt
from monitor_frames import MonitorFrames
import server

import time
import threading

# State machine implementation
class StateMachine(threading.Thread):

	# Timeout start values
	ACTIVITY_TIMEOUT = 10
	OVERRIDE_TIMEOUT = 10

	def __init__(self):
		# Initialize the activity of this thread (monitoring events)
		super(StateMachine, self).__init__(target=self.Main)

		# Initialize the condition variable used to signal events
		self.interrupt = Interrupt()

		# Initialize the red light blinking thread
		self.red_light_thread = None

	def Main(self):
		# Choose a starting state based on the current states of
		# LOWER_LIMIT and UPPER_LIMIT
		state_function = self.GetStartupState()
		
		# Infinite run cycle: run a state function, wait until it
		# returns another state function, and run that
		while True and state_function:
			print("Transitioning to {:}".format(state_function.__name__))
			state_function = state_function()

	def GetStartupState(self):
		# Get current states of LOWER_LIMIT and UPPER_LIMIT
		lower = fhgpio.Get(fhgpio.PIN_LOWER_LIMIT)
		upper = fhgpio.Get(fhgpio.PIN_UPPER_LIMIT)

		# Open and Raised
		if not lower and upper:
			return self.StateFunction_OpenAndRaised

		# Open and Raising
		elif not lower and not upper:
			return self.StateFunction_OpenAndRaising

		# Closed and Raised
		elif lower and upper:
			return self.StateFunction_ClosedAndRaised

		# Closed and Raising
		elif lower and not upper:
			return self.StateFunction_ClosedAndRaising

		else:
			return None

	def StateFunction_OpenAndRaised(self):
		# Set outputs
		fhgpio.Clear()

		# Blink red light to show activity
		def BlinkRed():
			fhgpio.Set(fhgpio.PIN_LED_R, True)
			time.sleep(0.5)
			fhgpio.Set(fhgpio.PIN_LED_R, False)

		if self.red_light_thread == None or type(self.red_light_thread) is threading.Thread and not self.red_light_thread.isAlive():
			self.red_light_thread = threading.Thread(target=BlinkRed)
			self.red_light_thread.start()

		# This is the absolute time at which the timeout should occur
		self.activity_timeout = time.time() + StateMachine.ACTIVITY_TIMEOUT

		while True:
			with self.interrupt:
				# Wait for a duration until the specified time arrives
				timed_out = not self.interrupt.wait(self.activity_timeout - time.time())
				event = self.interrupt.Read()

				if timed_out:
					return self.StateFunction_Closing

				elif event == Interrupt.EVENT_MANUAL_CLOSE:
					return self.StateFunction_Closing

				elif event == Interrupt.EVENT_SASH_CLOSED:
					return self.StateFunction_ClosedAndRaised

				elif event == Interrupt.EVENT_ACTIVITY:
					# Has the effect of resetting the timeout
					return self.StateFunction_OpenAndRaised

				elif event == Interrupt.EVENT_MANUAL_OVERRIDE:
					return self.StateFunction_OverriddenAndRaised

				elif event == Interrupt.EVENT_PUSHER_LEAVES_TOP:
					return self.StateFunction_OpenAndRaising

	def StateFunction_Closing(self):
		# Set outputs
		fhgpio.Clear()
		fhgpio.Set(fhgpio.PIN_MOTOR_DOWN, True)

		while True:
			with self.interrupt:
				self.interrupt.wait()
				event = self.interrupt.Read()

				if event == Interrupt.EVENT_SASH_CLOSED:
					return self.StateFunction_ClosedAndRaising

				elif event == Interrupt.EVENT_MANUAL_OVERRIDE:
					return self.StateFunction_OverriddenAndRaising

				elif event == Interrupt.EVENT_OBSTRUCTION:
					return self.StateFunction_OpenAndRaising

	def StateFunction_ClosedAndRaising(self):
		# Set outputs
		fhgpio.Clear()
		fhgpio.Set(fhgpio.PIN_MOTOR_UP, True)
		fhgpio.Set(fhgpio.PIN_LED_G, True)

		while True:
			with self.interrupt:
				self.interrupt.wait()
				event = self.interrupt.Read()

				if event == Interrupt.EVENT_SASH_OPENED:
					return self.StateFunction_OpenAndRaising

				elif event == Interrupt.EVENT_PUSHER_REACHES_TOP:
					return self.StateFunction_ClosedAndRaised

	def StateFunction_ClosedAndRaised(self):
		# Set outputs
		fhgpio.Clear()
		fhgpio.Set(fhgpio.PIN_LED_G, True)

		while True:
			with self.interrupt:
				self.interrupt.wait()
				event = self.interrupt.Read()

				if event == Interrupt.EVENT_SASH_OPENED:
					return self.StateFunction_OpenAndRaised

				elif event == Interrupt.EVENT_PUSHER_LEAVES_TOP:
					return self.StateFunction_ClosedAndRaising

	def StateFunction_OpenAndRaising(self):
		# Set outputs
		fhgpio.Clear()
		fhgpio.Set(fhgpio.PIN_MOTOR_UP, True)

		while True:
			with self.interrupt:
				self.interrupt.wait()
				event = self.interrupt.Read()

				if event == Interrupt.EVENT_PUSHER_REACHES_TOP:
					return self.StateFunction_OpenAndRaised

				elif event == Interrupt.EVENT_MANUAL_CLOSE:
					return self.StateFunction_Closing

				elif event == Interrupt.EVENT_MANUAL_OVERRIDE:
					return self.StateFunction_OverriddenAndRaising

				elif event == Interrupt.EVENT_SASH_CLOSED:
					return self.StateFunction_ClosedAndRaising

	def StateFunction_OverriddenAndRaising(self):
		# Set outputs
		fhgpio.Clear()
		fhgpio.Set(fhgpio.PIN_MOTOR_UP, True)
		fhgpio.Set(fhgpio.PIN_LED_R, True)
		fhgpio.Set(fhgpio.PIN_LED_G, True)

		while True:
			with self.interrupt:
				self.interrupt.wait()
				event = self.interrupt.Read()

				if event == Interrupt.EVENT_PUSHER_REACHES_TOP:
					return self.StateFunction_OverriddenAndRaised

				elif event == Interrupt.EVENT_SASH_CLOSED:
					return self.StateFunction_ClosedAndRaising

				elif event == Interrupt.EVENT_MANUAL_CLOSE:
					return self.StateFunction_Closing

	def StateFunction_OverriddenAndRaised(self):
		# Set outputs
		fhgpio.Clear()
		fhgpio.Set(fhgpio.PIN_LED_R, True)
		fhgpio.Set(fhgpio.PIN_LED_G, True)

		# This is the absolute time at which the timeout should occur
		self.override_timeout = time.time() + StateMachine.OVERRIDE_TIMEOUT

		while True:
			with self.interrupt:
				# Wait for a duration until the specified time arrives
				timed_out = not self.interrupt.wait(self.override_timeout - time.time())
				event = self.interrupt.Read()

				if timed_out:
					return self.StateFunction_OpenAndRaised

				elif event == Interrupt.EVENT_MANUAL_CLOSE:
					return self.StateFunction_Closing

				elif event == Interrupt.EVENT_SASH_CLOSED:
					return self.StateFunction_ClosedAndRaised

				elif event == Interrupt.EVENT_MANUAL_OVERRIDE:
					# Has the effect of resetting the timeout
					return self.StateFunction_OverriddenAndRaised

				elif event == Interrupt.EVENT_PUSHER_LEAVES_TOP:
					return self.StateFunction_OverriddenAndRaising

if __name__ == '__main__':
	fhgpio.Init()

	state_machine = StateMachine()
	state_machine.start()

	state_machine.interrupt.InitTriggers()

	camera = Camera()
	threading.Thread(target=camera.GetFrames).start()
	threading.Thread(target=MonitorFrames, args=(camera, state_machine.interrupt)).start()

	threading.Thread(target=server.RunServer, args=[camera]).start()
