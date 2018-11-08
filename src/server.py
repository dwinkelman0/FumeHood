import camera

import socketserver
from http import server

class Server(socketserver.ThreadingMixIn, server.HTTPServer):
	allow_reuse_address = True
	daemon_threads = True

class HTTPHandler(server.BaseHTTPRequestHandler):
	def do_GET(self):
		None

	def do_POST(self):
		None

	def ServeVideo(self):
		None
