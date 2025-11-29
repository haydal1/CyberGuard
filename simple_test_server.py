#!/usr/bin/env python3
import http.server
import socketserver
import json
import os

PORT = 8001

class TestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"📨 Received request: {self.path}")
        
        if self.path == '/test':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "OK", "message": "Server is working!"}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "ERROR", "message": "Endpoint not found"}
            self.wfile.write(json.dumps(response).encode())

# Kill any process using the port
os.system(f"fuser -k {PORT}/tcp > /dev/null 2>&1")
sleep 1

with socketserver.TCPServer(("", PORT), TestHandler) as httpd:
    print(f"🚀 Simple test server started on port {PORT}")
    print("📍 Test with: curl http://localhost:8001/test")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
