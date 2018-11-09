from picamera import PiCamera
from io import BytesIO
from threading import Condition
from time import sleep

class CameraStream(object):
	def __init__(self):
		'''Special stream implementation for capturing frames and
		passing them to other threads'''
		self.frame = None # Stores a frame array
		self.buffer = BytesIO() # The buffer this emulates
		self.cond_newframe = Condition() # Signals a new frame

	def write(self, buffer):
		'''Place new data into the stream'''
		# When a frame is written to this buffer, copy the new data to
		# a local variable and broadcast to dependent threads that
		# there is new data
		#if buffer.startswith(b"\xff\xd8"):
		self.buffer.truncate()
		with self.cond_newframe:
			self.frame = self.buffer.getvalue()
			self.cond_newframe.notify_all()
		self.buffer.seek(0)
		return self.buffer.write(buffer)

class Camera(object):
	def __init__(self):
		'''Object for controlling access to the RPi camera and the
		output stream'''
		# Create a camera object and configure basic properties
		self.camera = PiCamera(resolution=(480, 640), framerate=6)
		self.camera.rotation = 90

		# Create a stream to capture frames
		# Processes using the camera will hook into this stream's condition variable
		self.stream = CameraStream()

	def GetFrames(self):
		'''Loop for the camera to get frames and pass to the internal
		CameraStream; this is meant to be run in its own thread'''
		# Get frames forever
		self.camera.start_recording(self.stream, format="rgb")
		while True: sleep(1)
		self.camera.stop_recording()
