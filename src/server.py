import camera

import socketserver
from http import server

class CameraServer(socketserver.ThreadingMixIn, server.HTTPServer):
	allow_reuse_address = True
	daemon_threads = True

	def SetCameraStream(self, stream):
		'''Make the camera stream accessible to the HTTP Handler'''
		self.camera_stream = stream

class HTTPHandler(server.BaseHTTPRequestHandler):
	def do_GET(self):
		None

	def do_POST(self):
		None

	def ServeVideo(self):
		None
