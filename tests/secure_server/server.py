# Resources:
# https://blog.anvileight.com/posts/simple-python-http-server/
#
# To create keys and certificates:
#   openssl genrsa 1024 > host.key
#   chmod 400 host.key
#   openssl req -new -x509 -nodes -sha1 -days 365 -key host.key -out host.cert
#
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

	def do_GET(self):
		self.send_response(200)
		self.end_headers()
		self.wfile.write(b'Hello, world!')

httpd = HTTPServer(('localhost', 443), SimpleHTTPRequestHandler)

httpd.socket = ssl.wrap_socket (httpd.socket, 
        keyfile="host.key", 
        certfile='host.cert', server_side=True)

httpd.serve_forever()
