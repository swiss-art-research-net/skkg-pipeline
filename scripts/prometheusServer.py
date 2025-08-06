from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST, multiprocess
import os

# Use the same directory as set in PROMETHEUS_MULTIPROC_DIR
PROMETHEUS_MULTIPROC_DIR = os.environ.get("PROMETHEUS_MULTIPROC_DIR", "/logs/prometheus")

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path != "/metrics":
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not Found")
                return

            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
            data = generate_latest(registry)
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Internal server error: {e}".encode())

if __name__ == "__main__":
    port = 8000
    print(f"Starting metrics server on port {port}")
    server = HTTPServer(("0.0.0.0", port), MetricsHandler)
    server.serve_forever()