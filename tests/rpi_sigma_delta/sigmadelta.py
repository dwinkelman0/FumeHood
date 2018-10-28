# picamera library source can be found at
# https://github.com/waveform80/picamera
# Documentation can be found at
# picamera.readthedocs.io/en/release-1.13

from picamera import PiCamera
from time import sleep, time
from io import BytesIO
from PIL import Image
from numpy import asarray

# Initialize and warm up the camera
stream = BytesIO()
camera = PiCamera(resolution=(1296, 972), framerate=5)
sleep(2)

# Repeatedly capture frames to byte stream
n_frames = 0;
for frame in camera.capture_continuous(stream, format="jpeg"):
	print "Processing frame", n_frames
	stream.truncate()
	stream.seek(0)
	image = Image.open(stream)
	image.save("shot_cont_%.2d.png" % n_frames)

	# Break after a certain number of frames
	n_frames += 1
	if n_frames > 10:
		break

# Clean up
camera.close()
