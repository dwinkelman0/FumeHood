# picamera library source can be found at
# https://github.com/waveform80/picamera

from picamera import PiCamera
from time import sleep
from io import BytesIO
from PIL import Image
from numpy import asarray

# Initialize and warm up the camera
stream = BytesIO()
camera = PiCamera()
#camera.start_preview()
sleep(2)

# Capture frame to byte stream
camera.capture(stream, format='jpeg')
stream.seek(0)
image = Image.open(stream)
image.save("shot.png")

# Convert frame to a Numpy array
array = asarray(image)

# Clean up
camera.close()
