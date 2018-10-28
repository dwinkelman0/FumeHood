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
camera = PiCamera()
#camera.start_preview()
sleep(2)

# Capture frame to byte stream
t0 = time()
camera.capture(stream, format="bmp")
t1 = time()
print "Capture:", t1 - t0
stream.seek(0)
t2 = time()
image = Image.open(stream)
t3 = time()
print "Image.open():", t3 - t2
image.save("shot.png")
t4 = time()
print "Image.save():", t4 - t3

# Convert frame to a Numpy array
array = asarray(image)
t5 = time()
print "numpy.asarray():", t5 - t4

# Clean up
camera.close()
