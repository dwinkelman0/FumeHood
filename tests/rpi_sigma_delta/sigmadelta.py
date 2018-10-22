from picamera import PiCamera
from time import sleep
from io import BytesIO
from PIL import Image

# Initialize and warm up the camera
stream = BytesIO()
camera = PiCamera()
camera.start_preview()
camera.sleep(2)

# Capture frame to byte stream
camera.capture(stream, format='jpeg')
streak.seek(0)
image = Image.open(stream)

# Clean up
camera.stop_preview()

