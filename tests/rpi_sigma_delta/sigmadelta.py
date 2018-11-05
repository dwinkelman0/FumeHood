# Proof-of-concept test for sigma delta motion detection algorithm
# References:
# https://www.pyimagesearch.com/2015/03/30/accessing-the-raspberry-pi-camera-with-opencv-and-python/

from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import numpy as np

camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
camera.rotation = 90
raw_frame = PiRGBArray(camera, size=camera.resolution)

time.sleep(0.1)

last_image = None

for frame in camera.capture_continuous(raw_frame, format="bgr", use_video_port=True):
	image = frame.array
	print image.shape
	image = image.astype(int)
	if last_image is not None:
		difference = image - last_image
		sqr_difference = np.abs(difference)
		subtotal = np.sum(np.sum(sqr_difference))
		subtotal_long = subtotal.astype(np.int64)
		total = np.sum(subtotal_long)
		print "Weighted Difference:", np.log(total)
	last_image = image
	raw_frame.truncate(0)
