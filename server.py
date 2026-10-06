import os
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote

HOST = "0.0.0.0"
PORT = 8000
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")

os.makedirs(RESOURCE_DIR, exist_ok=True)

# Create a few demo folders so the server is immediately usable.
for folder in ("notes", "assignments", "materials"):
    os.makedirs(os.path.join(RESOURCE_DIR, folder), exist_ok=True)


class NetDeskHandler(BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_text(self, text, status=200):
        payload = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._send_json({
                "service": "NetDesk - Classroom Connectivity Assistant",
                "status": "online",
                "server": self.server.server_address[0],
                "port": PORT,
                "endpoints": [
                    "/status",
                    "/resources",
                    "/resources/<folder>/<file>"
                ]
            })
            return

        if path == "/status":
            self._send_json({
                "service": "NetDesk",
                "status": "online",
                "client_ip": self.client_address[0],
                "server_ip": get_server_ip(),
                "port": PORT
            })
            return

        if path == "/resources":
            self._list_resources()
            return

        if path.startswith("/resources/"):
            self._download_resource(path[len("/resources/"):])
            return

        self._send_json({"error": "Endpoint not found"}, 404)

    def _list_resources(self):
        result = {}

        for folder in sorted(os.listdir(RESOURCE_DIR)):
            folder_path = os.path.join(RESOURCE_DIR, folder)

            if not os.path.isdir(folder_path):
                continue

            files = []
            for name in sorted(os.listdir(folder_path)):
                file_path = os.path.join(folder_path, name)
                if os.path.isfile(file_path):
                    files.append({
                        "name": name,
                        "size": os.path.getsize(file_path)
                    })

            result[folder] = files

        self._send_json(result)

    def _download_resource(self, relative_path):
        # Prevent path traversal outside resources/.
        relative_path = unquote(relative_path).replace("\\", "/")
        requested = os.path.normpath(relative_path)

        if requested.startswith("../") or requested == ".." or os.path.isabs(requested):
            self._send_json({"error": "Invalid resource path"}, 400)
            return

        file_path = os.path.abspath(os.path.join(RESOURCE_DIR, requested))
        resource_root = os.path.abspath(RESOURCE_DIR)

        if not file_path.startswith(resource_root + os.sep):
            self._send_json({"error": "Invalid resource path"}, 400)
            return

        if not os.path.isfile(file_path):
            self._send_json({"error": "Resource not found"}, 404)
            return

        try:
            with open(file_path, "rb") as file:
                data = file.read()

            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{os.path.basename(file_path)}"'
            )
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        except OSError as exc:
            self._send_json({"error": str(exc)}, 500)

    def log_message(self, format, *args):
        print(f"[NetDesk] {self.address_string()} - {format % args}")


def get_server_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"


def main():
    server_ip = get_server_ip()

    print("=" * 55)
    print("NETDESK - CLASSROOM CONNECTIVITY ASSISTANT")
    print("=" * 55)
    print(f"Server IP : {server_ip}")
    print(f"Port      : {PORT}")
    print()
    print("Students/teachers on the same LAN can connect using:")
    print(f"http://{server_ip}:{PORT}")
    print()
    print(f"Shared resources folder: {RESOURCE_DIR}")
    print("Put notes, assignments and materials inside its subfolders.")
    print()
    print("Press Ctrl+C to stop the server.")
    print("=" * 55)

    server = ThreadingHTTPServer((HOST, PORT), NetDeskHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping NetDesk server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
