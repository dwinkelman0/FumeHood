from picamera.array import PiRGBArray
from picamera import PiCamera
import time

camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
raw_frame = PiRGBArray(camera, size=camera.resolution)

time.sleep(0.1)

for frame in camera.capture_continuous(raw_frame, format="bgr", use_video_port=True):
	image = frame.array
	print image
	raw_frame.truncate(0)
