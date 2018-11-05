from picamera.array import PiRGBArray
from picamera import PiCamera
import polygon
import numpy as np
from PIL import Image

camera = PiCamera(resolution = (480, 640))
camera.rotation = 90

polygon_file = open("camserver/points.json")
pts_str = polygon_file.read()
pts = [polygon.Point(i["x"], i["y"]) for i in eval(pts_str)]
print pts

shape = polygon.Polygon(pts)
mask = shape.GenerateMask(480, 640)

frame_number = 0
last_image = None
raw_frame = PiRGBArray(camera, size=camera.resolution)
for frame in camera.capture_continuous(raw_frame, format="bgr", use_video_port=True):
	image = frame.array
	image = np.multiply(image, mask)
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
	if (frame_number % 10) == 0:
		im = Image.fromarray(image.astype('uint8'))
		im.save("test_frames/image_%d.jpeg" % frame_number)
	frame_number += 1
	
