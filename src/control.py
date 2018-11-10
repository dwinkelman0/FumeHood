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

from camera import Camera
import polygon

import numpy as np
import threading
import time
import math

# Interrupt codes for the control thread
INTERRUPT_NONE = 0
INTERRUPT_ACTIVITY = 1
INTERRUPT_MANUAL_OVERRIDE = 2
INTERRUPT_SASH_CLOSED = 3

# GPIO pins

class ControlThread(threading.Thread):
	def __init__(self):
		super(ControlThread, self).__init__(target=self.Main)
		self.cond_interrupt = threading.Condition()
		self.interrupt_code = INTERRUPT_NONE

	def Main(self):
		while True:
			with self.cond_interrupt:
				# Wait until an interrupt is called
				self.cond_interrupt.wait()
				code = self.interrupt_code

				print("Activity Interrupt")

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
			current_frame = np.multiply(current_frame, mask)
		current_frame = current_frame.astype("int32")
		if last_frame is not None and last_frame.size != 0:
			difference = np.abs(current_frame - last_frame)
			subtotal = np.sum(np.sum(difference)).astype("int64")
			total = np.sum(subtotal) / mask_weight # Average change per pixel
			print("Activity: %.3f" % total)
			activity = total > 5 # Completely arbitrary
		else:
			activity = False

		if activity:
			# Send a signal to the control thread
			with control.cond_interrupt:
				control.interrupt_code = INTERRUPT_ACTIVITY
				control.cond_interrupt.notify_all()

def MonitorGPIO(control):
	'''Monitor GPIO inputs for manual override and motor encoder'''
	

def Main():
	# Create the main control thread
	control_thread = ControlThread()
	control_thread.start()

	# Create a camera with an enclosed frame stream
	camera = Camera()

	# Start the thread for camera frame capture
	threading.Thread(target=camera.GetFrames).start()

	# Start the frames processing thread
	threading.Thread(target=MonitorFrames, args=(camera, control_thread)).start()

if __name__ == "__main__":
	Main()
