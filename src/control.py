###############################################################################
# TEAM FUME HOOD
# Production Control Program
#
# Daniel Winkelman <ddw30@duke.edu>
# Duke University
# EGR 101
#
# Summary:
#   This is the central program responsible for the control flow of the fume
#   hood sash closing device. It monitors a camera for motion within a defined
#   region for motion. After a period where there is no motion, it powers a
#   motor to close the sash while continuing to monitor the region for motion
#   as well as keeping track of the sash's position. It also interacts with a
#   manual override mechanism.
#
#   This program uses an extensive system of interrupts. Interrupts, as we have
#   implemented them, are events that happen within a multithreaded program.
#   The GPIO library monitors pins and creates events when inputs change states,
#   and the camera frame handler creates events whenever enough change in the
#   frame's pixels is detected. These interrupts are selectively handled
#   depending on where the program is within its flow.

from camera import Camera
import polygon
import server

import RPi.GPIO as GPIO

import numpy as np
import threading
import time
import math

# Timeout preferences
#TIME_UNTIL_SASH_CLOSE = 3 * 60		# 3 minutes
#TIME_FOR_MANUAL_OVERRIDE = 10 * 60	# 10 minutes
TIME_UNTIL_SASH_CLOSE = 10
TIME_FOR_MANUAL_OVERRIDE = 5

# Interrupt codes for the control thread
INTERRUPT_NONE = 0
INTERRUPT_ACTIVITY = 1
INTERRUPT_MANUAL_OVERRIDE = 2

INTERRUPT_SASH_CLOSED = 4
INTERRUPT_SASH_NOT_CLOSED = 5
INTERRUPT_SASH_ENTIRELY_OPEN = 6
INTERRUPT_SASH_NOT_ENTIRELY_OPEN = 7

INTERRUPT_RAISE_SASH = 10
INTERRUPT_NOT_RAISE_SASH = 11

# GPIO pins
GPIO_OUT_LED_RED = 33
GPIO_OUT_LED_YELLOW = 35
GPIO_OUT_LED_GREEN = 37

GPIO_OUT_MOTOR_DOWN = 31
GPIO_OUT_MOTOR_UP = 29

GPIO_IN_BUTTON_RAISE = 32
GPIO_IN_BUTTON_SASH = 36
GPIO_IN_BUTTON_OVERRIDE = 38

class ControlThread(threading.Thread):
	def __init__(self):
		super(ControlThread, self).__init__(target=self.Main)

		# Initialize interrupts for multithreading
		self.cond_interrupt = threading.Condition()
		self.interrupt_code = INTERRUPT_NONE

		# Initialize blink red light thread
		self.cond_led = threading.Condition()
		self.led_thread = threading.Thread(target=self.LEDThread)
		self.led_thread.start()

	@staticmethod
	def BlinkLED(led, duration, cycles):
		'''Blink the LED on and off for a certain duration for a certain number of cycles'''
		for i in range(cycles):
			GPIO.output(led, GPIO.LOW)
			time.sleep(duration)
			GPIO.output(led, GPIO.HIGH)
			time.sleep(duration)

	def LEDThread(self):
		while True:
			GPIO.output(GPIO_OUT_LED_RED, GPIO.HIGH)
			with self.cond_led:
				if self.cond_led.wait():
					GPIO.output(GPIO_OUT_LED_RED, GPIO.LOW)
				while self.cond_led.wait(0.5):
					continue
			GPIO.output(GPIO_OUT_LED_RED, GPIO.HIGH)

	def GetInterruptCode(self):
		'''Get the code associated with the most recent interrupt (and reset)'''
		code = self.interrupt_code
		self.interrupt_code = INTERRUPT_NONE
		return code

	def IsSashClosed(self):
		'''Determine whether the sash is closed'''
		return GPIO.input(GPIO_IN_BUTTON_SASH)

	def CloseSash(self):
		'''Close the sash using the motor'''
		print("Close sash")
		# Start motor
		GPIO.output(GPIO_OUT_MOTOR_DOWN, GPIO.HIGH)
		while True:
			with self.cond_interrupt:
				self.cond_interrupt.wait()
				code = self.GetInterruptCode()
				if code == INTERRUPT_SASH_CLOSED:
					# The sash is closed: we are done
					# Stop motor
					GPIO.output(GPIO_OUT_MOTOR_DOWN, GPIO.LOW)
					break
				elif code == INTERRUPT_MANUAL_OVERRIDE:
					# Manual override engaged: stop motor
					# Stop motor
					GPIO.output(GPIO_OUT_MOTOR_DOWN, GPIO.LOW)
					self.WaitManualOverride()
					break
				elif code == INTERRUPT_RAISE_SASH:
					# The sash is to be raised per user instruction: engage motor in opposite direction
					# Stop motor
					GPIO.output(GPIO_OUT_MOTOR_DOWN, GPIO.LOW)
					self.OpenSash()
					break

	def OpenSash(self):
		'''Open the sash while the user presses the button'''
		print("Open sash")
		# Start motor
		GPIO.output(GPIO_OUT_MOTOR_UP, GPIO.HIGH)
		while True:
			with self.cond_interrupt:
				self.cond_interrupt.wait()
				code = self.GetInterruptCode()
				if code == INTERRUPT_SASH_ENTIRELY_OPEN:
					# The sash is completely open: we are done
					# Stop motor
					GPIO.output(GPIO_OUT_MOTOR_UP, GPIO.LOW)
					break
				elif code == INTERRUPT_MANUAL_OVERRIDE:
					# Manual override engaged: stop motor
					# Stop motor
					GPIO.output(GPIO_OUT_MOTOR_UP, GPIO.LOW)
					self.WaitManualOverride()
					break
				elif code == INTERRUPT_NOT_RAISE_SASH:
					# The raise sash button is no longer pressed
					# Stop motor
					GPIO.output(GPIO_OUT_MOTOR_UP, GPIO.LOW)
					break

	def WaitManualOverride(self):
		'''Wait until the manual override is done'''
		print("Manual Override")
		# Turn on yellow light until override done
		print("Wait Manual Override")
		GPIO.output(GPIO_OUT_LED_YELLOW, GPIO.LOW)
		release_time = time.time() + TIME_FOR_MANUAL_OVERRIDE
		while time.time() < release_time:
			with self.cond_interrupt:
				if self.cond_interrupt.wait(release_time - time.time()):
					if self.interrupt_code == INTERRUPT_MANUAL_OVERRIDE:
						release_time = time.time() + TIME_FOR_MANUAL_OVERRIDE
					elif self.interrupt_code == INTERRUPT_SASH_CLOSED:
						break
					elif self.interrupt_code == INTERRUPT_RAISE_SASH:
						# Turn off LED early
						GPIO.output(GPIO_OUT_LED_YELLOW, GPIO.HIGH)
						self.OpenSash()
						break
		GPIO.output(GPIO_OUT_LED_YELLOW, GPIO.HIGH)

	def WaitSashClosed(self):
		while self.IsSashClosed():
			print("Wait Sash Closed")
			# Turn on green LED while the sash is closed
			GPIO.output(GPIO_OUT_LED_GREEN, GPIO.LOW)

			with self.cond_interrupt:
				self.cond_interrupt.wait()
				code = self.GetInterruptCode()
				if code == INTERRUPT_RAISE_SASH:
					# User requesting sash raise
					GPIO.output(GPIO_OUT_LED_GREEN, GPIO.HIGH)
					self.OpenSash()
				elif code == INTERRUPT_SASH_NOT_CLOSED:
					# Sash is no longer closed
					break

		GPIO.output(GPIO_OUT_LED_GREEN, GPIO.HIGH)

	def Main(self):
		while True:
			# The sash is closed: wait until it is not closed anymore
			self.WaitSashClosed()

			# The sash is open: wait for something to happen
			with self.cond_interrupt:
				if self.cond_interrupt.wait(TIME_UNTIL_SASH_CLOSE):
					# An event happened
					code = self.GetInterruptCode()
					if code == INTERRUPT_MANUAL_OVERRIDE:
						self.WaitManualOverride()
						continue
					elif code == INTERRUPT_ACTIVITY:
						# Activity detected by the camera
						# Exit back to top of function and reset the wait
						# Blink the red light once
						#GPIO.output(GPIO_OUT_LED_RED, GPIO.LOW)
						#time.sleep(0.5)
						#GPIO.output(GPIO_OUT_LED_RED, GPIO.HIGH)
						#time.sleep(0.5)
						with self.cond_led:
							self.cond_led.notify_all()
						continue
					elif code == INTERRUPT_SASH_CLOSED:
						# The sash is closed
						# Exit back to top of function and wait until it is not closed
						continue
					elif code == INTERRUPT_RAISE_SASH:
						# User requesting sash raise
						self.OpenSash()
						continue
				else:
					# Nothing happened: close the sash
					self.CloseSash()

def MonitorFrames(camera, control):
	'''Compare current frame to last frame as they are generated'''

	# Storage for frames to compare
	current_frame, last_frame = None, None
	width, height = camera.camera.resolution

	# Generate mask for desired camera range
	mask = None
	try:
		# Try to read polygon from file and build a mask array
		with open("camserver/points.json") as polygon_file:
			print("Starting to create mask...")
			pts_str = polygon_file.read()
			pts = [polygon.Point(i["x"], i["y"]) for i in eval(pts_str)]
			shape = polygon.Polygon(pts)
			mask = shape.GenerateMask(width, height)

			# Slice only the part of the mask/frame that is relevant
			# Huge performance boost for processing
			x_coords, y_coords = [int(i.x) for i in pts], [int(i.y) for i in pts]
			mask_xmin, mask_xmax = min(x_coords), max(x_coords)
			mask_ymin, mask_ymax = min(y_coords), max(y_coords)
			# Ensure the slices are within domain
			mask_xmin, mask_xmax = max(mask_xmin, 0), min(mask_xmax, width - 1)
			mask_ymin, mask_ymax = max(mask_ymin, 0), min(mask_ymax, height - 1)
			mask = mask[mask_ymin:mask_ymax, mask_xmin:mask_xmax]

			mask_weight = np.sum(np.sum(np.sum(mask)))
			print("Created mask")
	except:
		print("Error with creating polygon mask")
		mask_weight = width * height * 3

	while True:
		with camera.stream.cond_newframe:
			# Wait for a new frame
			camera.stream.cond_newframe.wait()
			last_frame = current_frame
			# Cast frame into a numpy array
			current_frame = np.frombuffer(camera.stream.frame, dtype="uint8")

		# Make sure there was data in the buffer
		if current_frame.size != 0:
			current_frame.shape = (height, width, 3)
		else:
			continue

		# Perform sigma delta check
		if mask is not None:
			# Slice only the part of the mask/frame that is relevant
			# Huge performance boost for processing
			current_frame = current_frame[mask_ymin:mask_ymax, mask_xmin:mask_xmax]
			current_frame = np.multiply(current_frame, mask)
		current_frame = current_frame.astype("int32")
		if last_frame is not None and last_frame.size != 0:
			difference = np.square(current_frame - last_frame) # Non-linearity helps bring out meaningful changes
			subtotal = np.sum(np.sum(difference)).astype("int64")
			total = np.sum(subtotal) / mask_weight # Average change per pixel
			print("Activity: %.3f" % total)
			activity = total > 15 # Completely arbitrary
			# 15 (with the sqrare function) seems to avoid noise like ambiance/shadows,
			# but still plenty to detect even far-away motion
		else:
			activity = False

		if activity:
			# Send a signal to the control thread
			with control.cond_interrupt:
				control.interrupt_code = INTERRUPT_ACTIVITY
				control.cond_interrupt.notify_all()

def Interrupt(control, pin, rising_code=None, falling_code=None):
	with control.cond_interrupt:
		if GPIO.input(pin):
			# Rising transition ends on HIGH
			print("Rising %d" % pin)
			if rising_code is not None:
				control.interrupt_code = rising_code
				control.cond_interrupt.notify_all()
		else:
			# Falling transition ends on LOW
			print("Falling %d" % pin)
			if falling_code is not None:
				control.interrupt_code = falling_code
				control.cond_interrupt.notify_all()

def MonitorGPIO(control):
	'''Monitor GPIO inputs for manual override, sash raise, and sash limits'''

	GPIO.add_event_detect(GPIO_IN_BUTTON_SASH, GPIO.BOTH, lambda pin: Interrupt(control, pin, INTERRUPT_SASH_CLOSED, INTERRUPT_SASH_NOT_CLOSED))
	GPIO.add_event_detect(GPIO_IN_BUTTON_OVERRIDE, GPIO.BOTH, lambda pin: Interrupt(control, pin, None, INTERRUPT_MANUAL_OVERRIDE))
	GPIO.add_event_detect(GPIO_IN_BUTTON_RAISE, GPIO.BOTH, lambda pin: Interrupt(control, pin, INTERRUPT_NOT_RAISE_SASH, INTERRUPT_RAISE_SASH))

def SetupGPIO():
	'''Initialize the GPIO library and pins'''
	GPIO.setmode(GPIO.BOARD)

	GPIO.setup(GPIO_OUT_LED_RED, GPIO.OUT)
	GPIO.setup(GPIO_OUT_LED_YELLOW, GPIO.OUT)
	GPIO.setup(GPIO_OUT_LED_GREEN, GPIO.OUT)
	GPIO.setup(GPIO_OUT_MOTOR_DOWN, GPIO.OUT)
	GPIO.setup(GPIO_OUT_MOTOR_UP, GPIO.OUT)
	GPIO.setup(GPIO_IN_BUTTON_SASH, GPIO.IN)
	GPIO.setup(GPIO_IN_BUTTON_OVERRIDE, GPIO.IN)
	GPIO.setup(GPIO_IN_BUTTON_RAISE, GPIO.IN)

	GPIO.output(GPIO_OUT_LED_RED, GPIO.HIGH)
	GPIO.output(GPIO_OUT_LED_YELLOW, GPIO.HIGH)
	GPIO.output(GPIO_OUT_LED_GREEN, GPIO.HIGH)
	GPIO.output(GPIO_OUT_MOTOR_DOWN, GPIO.LOW)
	GPIO.output(GPIO_OUT_MOTOR_UP, GPIO.LOW)

def Main():
	# Initialize GPIO
	SetupGPIO()

	# Create the main control thread
	control_thread = ControlThread()
	control_thread.start()

	# Start listening to GPIO inputs
	# Perform on the main thread to continue program
	MonitorGPIO(control_thread)

	# Create a camera with an enclosed frame stream
	camera = Camera()

	# Start the thread for camera frame capture
	threading.Thread(target=camera.GetFrames).start()

	# Start the frames processing thread
	threading.Thread(target=MonitorFrames, args=(camera, control_thread)).start()

	# Start the server thread
	threading.Thread(target=server.RunServer, args=[camera]).start()

if __name__ == "__main__":
	Main()
