# LAB 2 PR: Concurrent HTTP Server

This lab extends the HTTP file server from Lab 1 by making it multithreaded to handle multiple concurrent connections. It includes a request counter with race condition demonstration and IP-based rate limiting.

## Overview

The server supports:
- **Multithreading**: Thread-per-request model for concurrent handling
- **Request Counter**: Tracks hits per file with thread-safe implementation
- **Rate Limiting**: Limits clients to 5 requests/second based on IP address
- **Race Condition Demo**: Demonstrates and prevents race conditions in concurrent counter updates

## Features

### 1. Multithreaded Server
- Uses threading to handle multiple requests simultaneously
- Each incoming connection spawns a new thread
- Significantly faster than single-threaded server for concurrent requests

### 2. Hit Counter
- Tracks number of times each file is requested
- Displays hit count in directory listing table
- Two modes:
  - **Naive mode** (`--unsafe-counter`): Demonstrates race conditions
  - **Thread-safe mode** (default): Uses locks to prevent race conditions

### 3. Rate Limiting
- Limits requests to 5 per second per client IP
- Thread-safe implementation using locks
- Returns HTTP 429 (Too Many Requests) when limit exceeded
- Includes `Retry-After: 1` header

### 4. Artificial Delay
- Optional `--delay` flag to simulate processing time
- Useful for demonstrating concurrency benefits

## Project Structure

```
Lab2/
├── server.py              # Multithreaded server with all features
├── test_performance.py    # Compare single vs multi-threaded performance
├── test_race_condition.py # Demonstrate race conditions in counter
├── test_rate_limiting.py  # Test rate limiting functionality
└── README.md             # This file
```

## Running the Server

### Basic Usage

```bash
python server.py <directory>
```

### Options

```bash
python server.py <directory> [OPTIONS]

Options:
  --single-threaded    Run in single-threaded mode (default: multi-threaded)
  --delay SECONDS      Add artificial delay to simulate work (default: 0)
  --unsafe-counter     Use naive counter without locks (for race condition demo)
  --race-demo          Add delays to force race conditions (for demonstration)
```

### Examples

**Multi-threaded server with 1 second delay:**
```bash
python server.py www --delay 1
```

**Single-threaded server for comparison:**
```bash
python server.py www --single-threaded --delay 1
```

**Demonstrate race conditions:**
```bash
python server.py www --unsafe-counter --race-demo
```

## Testing

### 1. Performance Comparison Test

Compare single-threaded vs multi-threaded server performance:

```bash
python test_performance.py
```

**Expected Results:**
- Single-threaded: ~10 seconds for 10 concurrent requests (1s delay each)
- Multi-threaded: ~1 second for 10 concurrent requests (parallel processing)
- Speedup: ~10x

**Test Procedure:**
1. Start server in single-threaded mode: `python server.py www --single-threaded --delay 1`
2. Run test and note results
3. Restart server in multi-threaded mode: `python server.py www --delay 1`
4. Run test again and compare

### 2. Race Condition Demonstration

Demonstrate race conditions in naive counter implementation:

```bash
python test_race_condition.py
```

**Test Procedure:**
1. Start server with unsafe counter: `python server.py www --unsafe-counter --race-demo`
2. Script makes 100 concurrent requests to same file
3. Check directory listing - hit count will be < 100 (race condition!)
4. Restart server with safe counter: `python server.py www --race-demo`
5. Script makes 100 concurrent requests again
6. Check directory listing - hit count will be exactly 100 (no race condition)

**Why Race Conditions Occur:**
```
Thread A: Read counter (10)
Thread B: Read counter (10)  ← Both read same value!
Thread A: Write counter (11)
Thread B: Write counter (11) ← Lost update from Thread A!
Result: 2 requests but counter only increased by 1
```

**How Locks Prevent This:**
- Only one thread can access counter at a time
- Other threads must wait
- All updates are preserved

### 3. Rate Limiting Test

Test IP-based rate limiting:

```bash
python test_rate_limiting.py
```

**Test Scenarios:**
1. **Normal user** (4 req/s): Stays under limit, all requests succeed
2. **Spammer** (unlimited): Exceeds limit, gets 429 errors
3. **Concurrent users**: Both tested simultaneously

**Expected Results:**
- Normal user: ~0% rate limited
- Spammer: ~90%+ rate limited
- Server throughput: Limited to ~5 requests/second per IP

## Implementation Details

### Threading Model

```python
# Thread-per-request model
while True:
    client_socket, addr = server_socket.accept()
    thread = threading.Thread(target=handle_client, args=(client_socket, addr, directory))
    thread.daemon = True
    thread.start()
```

### Counter Implementation

**Naive (Race Conditions):**
```python
def increment_counter(file_path):
    current = file_hit_counter[file_path]
    time.sleep(0.001)  # Simulate race condition
    file_hit_counter[file_path] = current + 1
```

**Thread-Safe (With Lock):**
```python
def increment_counter(file_path):
    with counter_lock:
        file_hit_counter[file_path] += 1
```

### Rate Limiting Implementation

```python
def check_rate_limit(client_ip: str) -> bool:
    with rate_limit_lock:
        now = time.time()
        # Remove old timestamps (>1 second old)
        rate_limit_data[client_ip] = [ts for ts in rate_limit_data[client_ip] 
                                       if now - ts < 1.0]
        
        # Check if limit exceeded
        if len(rate_limit_data[client_ip]) >= MAX_REQUESTS_PER_SECOND:
            return False
        
        # Add current timestamp
        rate_limit_data[client_ip].append(now)
        return True
```

## Directory Listing with Hit Counter

The server displays a table showing files with their hit counts:

```
File / Directory          Hits
-------------------------+------
index.html               132
doc.pdf                  86
image.png                174
Pearson/                 59
```

## HTTP Responses

### Success (200 OK)
```http
HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 1234
```

### Rate Limited (429 Too Many Requests)
```http
HTTP/1.1 429 Too Many Requests
Content-Type: text/html
Content-Length: 234
Retry-After: 1
```

## Requirements

- Python 3.7+
- Standard library only (no external dependencies for server)
- `requests` library for test scripts:
  ```bash
  pip install requests
  ```

## Performance Results

### Test Configuration
- 10 concurrent requests
- 1 second delay per request
- Test file: `index.html`

### Single-Threaded Server
- Total time: ~10.5 seconds
- Throughput: ~0.95 requests/second
- Requests handled sequentially

### Multi-Threaded Server
- Total time: ~1.2 seconds
- Throughput: ~8.3 requests/second
- Requests handled in parallel
- **Speedup: ~8.75x**

## Race Condition Results

### Unsafe Counter (No Locks)
- 100 concurrent requests sent
- Expected hit count: 100
- Actual hit count: 14-30 (varies)
- **Lost updates: 70-86 (70-86%)**

### Safe Counter (With Locks)
- 100 concurrent requests sent
- Expected hit count: 100
- Actual hit count: 100
- **Lost updates: 0 (0%)**

## Rate Limiting Results

### Spammer (Unlimited Rate)
- Requests sent: 200
- Successful: 5
- Rate limited (429): 195
- Success rate: 2.5%

### Normal User (4 req/s)
- Requests sent: 200
- Successful: 200
- Rate limited (429): 0
- Success rate: 100%

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────┐
│     Main Server Thread           │
│  - Accept connections            │
│  - Spawn handler threads         │
└──────────────┬───────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌──────────┐    ┌──────────┐
│ Thread 1 │    │ Thread 2 │  ... (one per request)
└────┬─────┘    └────┬─────┘
     │               │
     ▼               ▼
┌─────────────────────────────┐
│   Shared Resources          │
│  - Hit Counter (with lock)  │
│  - Rate Limiter (with lock) │
└─────────────────────────────┘
```

## Thread Safety

All shared resources are protected by locks:

1. **Counter Lock**: Protects `file_hit_counter` dictionary
2. **Rate Limit Lock**: Protects `rate_limit_data` dictionary

Without locks, concurrent access causes:
- Race conditions
- Lost updates
- Incorrect counts

## Future Improvements

- Thread pool instead of thread-per-request
- Connection keepalive
- Request logging
- Configuration file
- Per-endpoint rate limits
- Redis-based rate limiting for distributed systems

## Troubleshooting

**Port already in use:**
```bash
# Find process using port 8080
netstat -ano | findstr :8080
# Kill the process
taskkill /PID <pid> /F
```

**Requests timing out:**
- Check firewall settings
- Increase timeout in test scripts
- Reduce concurrent request count

**Counter not updating:**
- Make sure you're requesting files, not directories
- Check that `USE_THREAD_SAFE_COUNTER = True`

## References

- Python threading: https://docs.python.org/3/library/threading.html
- HTTP status codes: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
- Rate limiting: https://en.wikipedia.org/wiki/Rate_limiting

## Author

Vladlen Mitu
Lab 2 - Concurrent HTTP Server
Networks & Protocols Course
