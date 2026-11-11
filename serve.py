"""Local preview server for the Armoseal site.

Same as `python3 -m http.server`, but tells the browser not to keep old
copies of pages and images, so every change shows up on a normal refresh.

Run:  python3 serve.py        then open http://localhost:8080
"""
import http.server
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    with http.server.ThreadingHTTPServer(("", PORT), NoCacheHandler) as httpd:
        print(f"Serving the site at http://localhost:{PORT}")
        httpd.serve_forever()
