import socket
import sys
import os
import mimetypes
import urllib.parse
import threading
import time
from collections import defaultdict
from datetime import datetime

# File types we allow to serve; other types return 404
ALLOWED_MIME = {"text/html", "image/png", "application/pdf"}

# Global counter for file access (with thread-safe option)
file_hit_counter = defaultdict(int)
counter_lock = threading.Lock()

# Rate limiting structures
rate_limit_data = defaultdict(list)  # IP -> list of request timestamps
rate_limit_lock = threading.Lock()
MAX_REQUESTS_PER_SECOND = 5

# Configuration flags
USE_THREAD_SAFE_COUNTER = True  # Set to False to demonstrate race conditions
SIMULATE_RACE_CONDITION = False  # Set to True to force race conditions

def build_response(status_code: int, reason: str, headers: dict, body: bytes) -> bytes:
    """Build a raw HTTP/1.1 response (status line + headers + body)."""
    lines = [f"HTTP/1.1 {status_code} {reason}"]
    for k, v in headers.items():
        lines.append(f"{k}: {v}")
    head = "\r\n".join(lines) + "\r\n\r\n"
    return head.encode() + (body or b"")

def not_found_response() -> bytes:
    """Return a minimal 404 Not Found HTML response with Content-Length."""
    body = b"<html><body><h1>404 Not Found</h1></body></html>"
    return build_response(404, "Not Found", {"Content-Type": "text/html", "Content-Length": str(len(body))}, body)

def generate_directory_listing(root_dir: str, rel_path: str) -> bytes:
    """Generate an HTML directory listing for rel_path under root_dir and return as HTTP 200."""
    # rel_path is relative to root_dir without leading slash
    safe_rel = rel_path.strip("/")
    abs_dir = os.path.join(root_dir, safe_rel)
    try:
        names = os.listdir(abs_dir)
    except OSError:
        return not_found_response()

    # Custom ordering: index.html first, then doc.pdf, then image.png, then the rest (alphabetically)
    priority = {"index.html": 0, "doc.pdf": 1, "image.png": 2}
    def sort_key(name: str):
        lname = name.lower()
        return (priority.get(lname, 10), lname)
    items = sorted(names, key=sort_key)

    title_path = "/" + (safe_rel + "/" if safe_rel else "")
    lines = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'><title>Index of " + title_path + "</title>",
        "<style>body{font-family:system-ui,Segoe UI,Arial} a{text-decoration:none} li{margin:4px 0}</style>",
        "</head><body>",
        f"<h1>Index of {title_path}</h1>",
        "<ul>",
    ]
    # Parent directory link if not root
    if safe_rel:
        parent = os.path.dirname(safe_rel)
        parent_href = "/" + (urllib.parse.quote(parent) + "/" if parent else "")
        lines.append(f"<li>📁 <a href=\"{parent_href}\">Parent Directory</a></li>")

    for name in items:
        item_rel = (safe_rel + "/" if safe_rel else "") + name
        item_abs = os.path.join(root_dir, item_rel)
        is_dir = os.path.isdir(item_abs)
        display = name + ("/" if is_dir else "")
        href = "/" + urllib.parse.quote(item_rel) + ("/" if is_dir else "")
        icon = "📁" if is_dir else "📄"
        lines.append(f"<li>{icon} <a href=\"{href}\">{display}</a></li>")
    lines += ["</ul>", "</body></html>"]
    body = "\n".join(lines).encode("utf-8")
    return build_response(200, "OK", {"Content-Type": "text/html", "Content-Length": str(len(body))}, body)

def serve_path(client_socket, root_dir: str, raw_path: str):
    """Serve a file or directory listing for the requested path; block traversal and unknown types."""
    # Decode URL and normalize path
    unquoted = urllib.parse.unquote(raw_path)
    rel = unquoted.lstrip("/")

    root_real = os.path.realpath(root_dir)
    abs_path = os.path.realpath(os.path.join(root_real, rel))

    # Prevent directory traversal
    if not (abs_path == root_real or abs_path.startswith(root_real + os.sep)):
        client_socket.sendall(not_found_response())
        return

    # If path is a directory (or root), return listing
    if rel == "" or os.path.isdir(abs_path):
        response = generate_directory_listing(root_real, rel)
        client_socket.sendall(response)
        return

    # Serve file if exists and allowed
    if not os.path.exists(abs_path):
        client_socket.sendall(not_found_response())
        return

    mime_type, _ = mimetypes.guess_type(abs_path)
    if mime_type not in ALLOWED_MIME:
        client_socket.sendall(not_found_response())
        return

    with open(abs_path, "rb") as f:
        body = f.read()
    response = build_response(200, "OK", {"Content-Type": mime_type, "Content-Length": str(len(body))}, body)
    client_socket.sendall(response)

def run_server(directory, host="0.0.0.0", port=8080):
    """Start a simple sequential HTTP server serving files from 'directory' on host:port."""
    # Create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Fix "OSError: Address already in use" without it, i would receive OSError, because OS keeps the old connection for a while
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"Serving {directory} on {host}:{port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")

        request = client_socket.recv(1024).decode(errors="ignore")
        print("Request:", request)

        # Parse request
        try:
            path = request.split()[1]
        except IndexError:
            path = "/"

        serve_path(client_socket, directory, path)

        client_socket.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python server.py <directory>")
        sys.exit(1)
    run_server(sys.argv[1])
