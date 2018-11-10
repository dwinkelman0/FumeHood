import camera

import json
import logging
import socketserver
from http import server
from PIL import Image
from io import BytesIO
import numpy as np
import traceback

class CameraServer(socketserver.ThreadingMixIn, server.HTTPServer):
	allow_reuse_address = True
	daemon_threads = True

	def SetCamera(self, camera):
		'''Make the camera stream accessible to the HTTP Handler'''
		self.camera = camera

# Import code
with open("camserver/index.html") as file_index:
	CONTENT_INDEX = file_index.read()
with open("camserver/script.js") as file_script:
	CONTENT_SCRIPT = file_script.read()
with open("camserver/style.css") as file_style:
	CONTENT_STYLE = file_style.read()

class HTTPHandler(server.BaseHTTPRequestHandler):
	def ServeFile(self, content, content_type):
		encoded_content = content.encode("utf-8")
		self.send_response(200)
		self.send_header("Content-Type", content_type)
		self.send_header("Content-Length", len(encoded_content))
		self.end_headers()
		self.wfile.write(encoded_content)

	def do_GET(self):

		# Redirect if user is at server root
		if self.path == "/":
			self.send_response(301)
			self.send_header("Location", "/index.html")
			self.end_headers()

		# Serve standard web content
		elif self.path == "/index.html":
			self.ServeFile(CONTENT_INDEX, "text/html")
		elif self.path == "/script.js":
			self.ServeFile(CONTENT_SCRIPT, "text/javascript")
		elif self.path == "/style.css":
			self.ServeFile(CONTENT_STYLE, "text/css")

		# Serve camera stream
		elif self.path == "/stream.mjpeg":
			self.send_response(200)
			self.send_header("Age", 0)
			self.send_header("Cache-Control", "no-cache, private")
			self.send_header("Pragma", "no-cache")
			self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=FRAME")
			self.end_headers()
			try:
				while True:
					with self.server.camera.stream.cond_newframe:
						# Wait for a new frame
						self.server.camera.stream.cond_newframe.wait()
						frame = self.server.camera.stream.frame
					# Convert frame to jpeg
					array = np.frombuffer(frame, dtype="uint8")
					width, height = self.server.camera.camera.resolution
					array.shape = (height, width, 3)
					image = Image.fromarray(array)
					bytes = BytesIO()
					image.save(bytes, format="jpeg")
					self.wfile.write(b"--FRAME\r\n")
					self.send_header("Content-Type", "image/jpeg")
					self.send_header("Content-Length", bytes.getbuffer().nbytes)
					self.end_headers()
					self.wfile.write(bytes.getvalue())
					self.wfile.write(b"\r\n")
			except Exception as e:
				logging.warning("Removed streaming client %s: %s", self.client_address, str(e))
				print(traceback.format_exc())

		# Serve JSON data for polygon
		elif self.path == "/polygon.json":
			try:
				with open("camserver/points.json") as json_file:
					points_list = eval(json_file.read())
			except:
				points_list = []
			json_str = json.dumps(points_list)
			self.ServeFile(json_str, "text/json")

		# 404 error if page not found
		else:
			self.send_error(404)
			self.end_headers()

	def do_POST(self):

		# Save polygon points to file
		if self.path == "/save-polygon":
			# Send confirmation
			self.send_response(200)
			self.end_headers()
			# Save JSON to file as-is
			n_content = int(self.headers["Content-Length"])
			data_str = str(eval(self.rfile.read(n_content)))
			with open("camserver/points.json", "w") as json_file:
				json_file.write(data_str)

		# 403 error if the address is wrong
		else:
			self.send_response(403)
			self.end_headers()

def RunServer(camera):
	address = ("", 8000)
	server = CameraServer(address, HTTPHandler)
	server.SetCamera(camera)
	server.serve_forever()
