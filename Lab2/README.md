# Lab 1: Simple HTTP File Server (TCP sockets)

This project implements a minimal HTTP server using raw TCP sockets and a small HTTP client script.

## Features
- Serves files from a directory passed as a command-line argument
- Supports HTML, PNG, and PDF
- Generates directory listings for folders (nested directories supported)
- Safe path normalization to prevent directory traversal
- Returns 404 for unknown types or missing files
- SO_REUSEADDR enabled for quick restarts
- Dockerfile and Docker Compose provided

## Server Usage

Local run (Windows PowerShell):

```powershell
python .\server.py .\www
```

Browse: http://localhost:8080/

## Client Usage

Downloads and prints based on content-type.

```powershell
python .\client.py 127.0.0.1 8080 / subdir
python .\client.py 127.0.0.1 8080 /index.html .
python .\client.py 127.0.0.1 8080 /image.png .\downloads
python .\client.py 127.0.0.1 8080 /docs/file.pdf .\downloads
```

- If HTML: prints body
- If PNG/PDF: saves to target directory

## Docker

Build:
```powershell
docker build -t lab1-server .
```
Run:
```powershell
docker run --rm -p 8080:8080 lab1-server
```

## Docker Compose

Compose file `compose.yaml` provided.

```powershell
docker compose up --build
# Stop
docker compose down
```

Uncomment the volumes section in `compose.yaml` to mount local `www` for live editing.

## Notes
- Directory listings show folders and files with clickable links.
- For a missing resource or unsupported type, the server returns HTTP 404.
- The server handles one request at a time (sequential).

## HTTP testing
- Directory listing (prints HTML)
```powershell
curl http://localhost:8080/
```

- Subfolder listing
```powershell
curl http://localhost:8080/reports/
curl http://localhost:8080/urus/
```

- Show only headers
```powershell
curl -I http://localhost:8080/
```

- Download a PDF and PNG
```powershell
curl http://localhost:8080/reports/week1.pdf -o .\week1.pdf
curl http://localhost:8080/urus/urus1.png -o .\urus1.png
```
