from camera import Camera
from fumehood_gpio import FumeHoodGPIO as fhgpio
from interrupts import Interrupt
from monitor_frames import MonitorFrames
import server

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

	def Main(self):
		# Choose a starting state based on the current states of
		# LOWER_LIMIT and UPPER_LIMIT
		state_function = self.GetStartupState()
		
		# Infinite run cycle: run a state function, wait until it
		# returns another state function, and run that
		while True and state_function:
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

		while True:
			with self.interrupt:
				timed_out = not self.interrupt.wait(StateMachine.ACTIVITY_TIMEOUT)
				event = self.interrupt.Read()

				if timed_out:
					return self.StateFunction_Closing

				elif event == Interrupt.EVENT_MANUAL_CLOSE:
					return self.StateFunction_Closing

				elif event == Interrupt.EVENT_SASH_CLOSED:
					return self.StateFunction_ClosedAndRaised

				elif event == Interrupt.EVENT_ACTIVITY:
					return self.StateFunction_OpenAndRaised

				elif event == Interrupt.MANUAL_OVERRIDE:
					return self.StateFunction_OverriddenAndRaised

	def StateFunction_Closing(self):
		return None

	def StateFunction_ClosedAndRaising(self):
		return None

	def StateFunction_ClosedAndRaised(self):
		return None

	def StateFunction_OpenAndRaising(self):
		return None

	def StateFunction_OverriddenAndRaising(self):
		return None

	def StateFunction_OverriddenAndRaised(self):
		return None

if __name__ == '__main__':
	#fhgpio.Init()

	state_machine = StateMachine()
	#state_machine.start()

	#state_machine.interrupt.InitTriggers()

	camera = Camera()
	threading.Thread(target=camera.GetFrames).start()
	threading.Thread(target=MonitorFrames, args=(camera, state_machine.interrupt)).start()

	threading.Thread(target=server.RunServer, args=[camera]).start()
