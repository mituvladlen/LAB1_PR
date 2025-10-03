import socket
import sys
import os
import mimetypes

def serve_file(client_socket, filepath):
    if not os.path.exists(filepath):
        # 404 response
        response = b"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n"
        response += b"<html><body><h1>404 Not Found</h1></body></html>"
        client_socket.sendall(response)
        return

    # Determine MIME type (HTML, PNG, PDF supported, otherwise 404)
    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type not in ["text/html", "image/png", "application/pdf"]:
        response = b"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n"
        response += b"<html><body><h1>404 Not Found</h1></body></html>"
        client_socket.sendall(response)
        return

    # Send file with headers
    with open(filepath, "rb") as f:
        body = f.read()
    header = f"HTTP/1.1 200 OK\r\nContent-Type: {mime_type}\r\nContent-Length: {len(body)}\r\n\r\n"
    client_socket.sendall(header.encode() + body)

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
            filename = request.split()[1].lstrip("/")
        except IndexError:
            filename = ""

        filepath = os.path.join(directory, filename if filename else "index.html")

        serve_file(client_socket, filepath)

        client_socket.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python server.py <directory>")
        sys.exit(1)
    run_server(sys.argv[1])
