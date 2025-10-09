import socket
import sys
import os
import mimetypes
import urllib.parse

ALLOWED_MIME = {"text/html", "image/png", "application/pdf"}

def build_response(status_code: int, reason: str, headers: dict, body: bytes) -> bytes:
    lines = [f"HTTP/1.1 {status_code} {reason}"]
    for k, v in headers.items():
        lines.append(f"{k}: {v}")
    head = "\r\n".join(lines) + "\r\n\r\n"
    return head.encode() + (body or b"")

def not_found_response() -> bytes:
    body = b"<html><body><h1>404 Not Found</h1></body></html>"
    return build_response(404, "Not Found", {"Content-Type": "text/html", "Content-Length": str(len(body))}, body)

def generate_directory_listing(root_dir: str, rel_path: str) -> bytes:
    # rel_path is relative to root_dir without leading slash
    safe_rel = rel_path.strip("/")
    abs_dir = os.path.join(root_dir, safe_rel)
    try:
        items = sorted(os.listdir(abs_dir))
    except OSError:
        return not_found_response()

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
