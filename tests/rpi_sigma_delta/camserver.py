# References:
# https://randomnerdtutorials.com/video-streaming-with-raspberry-pi-camera/
#
# README: Steps for usage
#  1. use `ifconfig -a` in the terminal to get this device's local ip address
#  2. run this program in the background
#  3. to view the whole page, go to <ip_address>:8000
#  4. to view the camera stream, to to <ip_address>:8000/stream.mjpg
#

import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server

file_index = open("camserver/index.html", "r")
file_script = open("camserver/script.js", "r")
file_style = open("camserver/style.css", "r")
CONTENT_INDEX = file_index.read()
CONTENT_SCRIPT = file_script.read()
CONTENT_STYLE = file_style.read()
file_index.close()
file_script.close()
file_style.close()

# Mockup class for an IO stream
class StreamingOutput(object):
	def __init__(self):
		self.frame = None
		self.buffer = io.BytesIO()
		self.condition = Condition()

	def write(self, buffer):
		if buffer.startswith(b"\xff\xd8"):
			self.buffer.truncate()
			with self.condition:
				self.frame = self.buffer.getvalue()
				self.condition.notify_all()
			self.buffer.seek(0)
		return self.buffer.write(buffer)

class StreamingHandler(server.BaseHTTPRequestHandler):
	def do_GET(self):
		if self.path == '/':
			self.send_response(301)
			self.send_header('Location', '/index.html')
			self.end_headers()
		elif self.path == '/index.html':
			content = CONTENT_INDEX.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', len(content))
			self.end_headers()
			self.wfile.write(content)
		elif self.path == '/stream.mjpg':
			self.send_response(200)
			self.send_header('Age', 0)
			self.send_header('Cache-Control', 'no-cache, private')
			self.send_header('Pragma', 'no-cache')
			self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
			self.end_headers()
			self.Stream()
		elif self.path == '/script.js':
			content = CONTENT_SCRIPT.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/javascript')
			self.send_header('Content-Length', len(content))
			self.end_headers()
			self.wfile.write(content)
		elif self.path == '/style.css':
			content = CONTENT_STYLE.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/css')
			self.send_header('Content-Length', len(content))
			self.end_headers()
			self.wfile.write(content)
		else:
			self.send_error(404)
			self.end_headers()

	def Stream(self):
		try:
			while True:
				with output.condition:
					output.condition.wait()
					frame = output.frame
				self.wfile.write(b'--FRAME\r\n')
				self.send_header('Content-Type', 'image/jpeg')
				self.send_header('Content-Length', len(frame))
				self.end_headers()
				self.wfile.write(frame)
				self.wfile.write(b'\r\n')
		except Exception as e:
			logging.warning("Removed streaming client %s: %s", self.client_address, str(e))

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
	allow_reuse_address = True
	daemon_threads = True

with picamera.PiCamera(resolution=(480, 640), framerate=24) as camera:
	output = StreamingOutput()
	camera.rotation = 90
	camera.start_recording(output, format='mjpeg')
	try:
		address = ('', 8000)
		server = StreamingServer(address, StreamingHandler)
		server.serve_forever()
	finally:
		camera.stop_recording()
