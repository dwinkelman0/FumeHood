# References:
# https://randomnerdtutorials.com/video-streaming-with-raspberry-pi-camera/
#   (Ripped off from https://github.com/waveform80/picamera/blob/master/docs/examples/web_streaming.py)
# https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7
#
# README:
# Steps for usage
#  1. use `ifconfig -a` in the terminal to get this device's local ip address
#  2. run this program in the background
#  3. to view the whole page, go to <ip_address>:8000
#  4. to view the camera stream, to to <ip_address>:8000/stream.mjpg
#
# Serves:
#  * Basic web resources (index.html, script.js, style.css)
#  * Continuously refreshing image (stream.mjpg)
#  * GET and POST requests for the JSON data that defines the polygon
#

import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server
import json

# Import code
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
			# When the user gets to the IP address, transfer to index page
			self.send_response(301)
			self.send_header('Location', '/index.html')
			self.end_headers()

		elif self.path == '/index.html':
			# Serve the index page
			content = CONTENT_INDEX.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', len(content))
			self.end_headers()
			self.wfile.write(content)

		elif self.path == '/stream.mjpg':
			# Serve the stream image
			# The image refreshes constantly, so it appears as a video
			self.send_response(200)
			self.send_header('Age', 0)
			self.send_header('Cache-Control', 'no-cache, private')
			self.send_header('Pragma', 'no-cache')
			self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
			self.end_headers()
			self.Stream()

		elif self.path == '/script.js':
			# Serve the index page's script
			content = CONTENT_SCRIPT.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/javascript')
			self.send_header('Content-Length', len(content))
			self.end_headers()
			self.wfile.write(content)

		elif self.path == '/style.css':
			# Serve the index page's stylesheet
			content = CONTENT_STYLE.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/css')
			self.send_header('Content-Length', len(content))
			self.end_headers()
			self.wfile.write(content)

		elif self.path == '/polygon.json':
			# Serve the stored polygon
			# Load the file (if it exists) and transform into a list
			try:
				f = open("camserver/points.json")
				points_str = f.read()
				f.close()
			except:
				points_str = "[]"
			points_list = eval(points_str)
			# Print the data as JSON and return
			json_str = json.dumps(points_list)
			content = json_str.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/json')
			self.send_header('Content-Length', len(content))
			self.end_headers()
			self.wfile.write(content)

		else:
			# 404 error if the page is not found
			self.send_error(404)
			self.end_headers()

	def do_POST(self):
		if self.path == '/save-polygon':
			# Receive polygon points to save to file
			self.send_response(200)
			self.end_headers()
			# Save JSON to file as-is
			n_content = int(self.headers['Content-Length'])
			data_str = str(eval(self.rfile.read(n_content)))
			file_json = open("camserver/points.json", "w")
			file_json.write(str(data_str))
			file_json.close()

		else:
			# 403 error (a.k.a. forbidden) if the address is wrong
			self.send_response(403)
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
	# Capture camera frames to stream
	camera.start_recording(output, format='mjpeg')
	try:
		address = ('', 8000)
		server = StreamingServer(address, StreamingHandler)
		server.serve_forever()
	finally:
		camera.stop_recording()
