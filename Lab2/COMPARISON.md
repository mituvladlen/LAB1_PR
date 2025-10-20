# Lab 2 Implementation Comparison

## Your Colleague's Implementation (Victoria)

### Key Features Analyzed:

#### 1. **Server Structure** (`server_mt.py`)
- Uses thread-per-request model
- PORT: 8001 (configurable via environment)
- MAX_WORKERS: 16 (though not using thread pool)
- 0.5s artificial delay for testing

#### 2. **Counter Implementation**
```python
COUNTS: Dict[str, int] = {}
COUNTS_LOCK = threading.Lock()

def _bump_count(path_key: str):
    with COUNTS_LOCK:
        current = COUNTS.get(path_key, 0)
        time.sleep(100 / 1000.0)  # 100ms delay for race demo
        COUNTS[path_key] = current + 1
```
- Thread-safe with lock
- Includes intentional delay to demonstrate race conditions
- Bumps count on every request to a path

#### 3. **Rate Limiting Implementation**
```python
REQUESTS_PER_SECOND = 5
TIME_WINDOW = 1.0
client_requests: Dict[str, List[float]] = {}
requests_lock = threading.Lock()

def allow_request(ip: str) -> bool:
    now = time.time()
    with requests_lock:
        if ip not in client_requests:
            client_requests[ip] = []
        
        timestamps = client_requests[ip]
        # Clean old timestamps beyond window
        client_requests[ip] = [t for t in timestamps if now - t < TIME_WINDOW]
        
        # Check limit
        if len(client_requests[ip]) < REQUESTS_PER_SECOND:
            client_requests[ip].append(now)
            return True
        return False
```
- Sliding window algorithm
- Thread-safe with lock
- Returns 429 status with custom HTML page

#### 4. **Directory Listing**
- Shows 4 columns: Name, Size, Last Modified, **Hits**
- Beautiful styling with pink theme ("Victoria's 2nd PR LAB")
- Uses Pixelify Sans font for title
- Hit counter displayed for each file

#### 5. **Testing Script** (`request_test.py`)
```python
def make_request(url, request_id, results, lock):
    # Makes request and records timing
    # Stores results in thread-safe list

def run_concurrent_test(url, num_requests, delay_between):
    # Creates threads for concurrent requests
    # Optional delay between thread creation
    # Calculates statistics (success rate, throughput, etc.)
```
- Command line interface: `python request_test.py <ip> <port> <path> <nr_req> [delay]`
- Supports optional delay between requests
- Detailed statistics output
- Thread-safe results collection

#### 6. **Docker Setup**
```dockerfile
# Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY server_mt.py request_test.py ./
ENV PORT=8001
EXPOSE 8001
CMD ["python", "server_mt.py", "/serve"]
```

```yaml
# docker-compose.yml
services:
  server2:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    volumes:
      - ./:/serve:ro
    command: ["python", "server_mt.py", "/serve"]

  requesttest:
    build:
      context: .
      dockerfile: Dockerfile
    entrypoint: ["python", "request_test.py"]
```

## Your Implementation

### Key Features Implemented:

#### 1. **Flexible Server Modes**
- Supports both single-threaded and multi-threaded modes
- Configurable via command-line flags
- Default: multi-threaded

#### 2. **Counter with Two Modes**
```python
USE_THREAD_SAFE_COUNTER = True  # Flag to toggle
SIMULATE_RACE_CONDITION = False  # Flag to force race conditions

def increment_counter(file_path: str):
    if USE_THREAD_SAFE_COUNTER:
        with counter_lock:
            if SIMULATE_RACE_CONDITION:
                current = file_hit_counter[file_path]
                time.sleep(0.001)
                file_hit_counter[file_path] = current + 1
            else:
                file_hit_counter[file_path] += 1
    else:
        # Naive implementation - race conditions possible
        if SIMULATE_RACE_CONDITION:
            current = file_hit_counter[file_path]
            time.sleep(0.001)
            file_hit_counter[file_path] = current + 1
        else:
            file_hit_counter[file_path] += 1
```
- Can demonstrate both safe and unsafe implementations
- Command-line flags: `--unsafe-counter`, `--race-demo`

#### 3. **Rate Limiting**
- Same sliding window algorithm as colleague
- 5 requests/second per IP
- Thread-safe implementation
- Returns 429 with Retry-After header

#### 4. **Comprehensive Testing Suite**
- `test_performance.py`: Compare single vs multi-threaded
- `test_race_condition.py`: Demonstrate race conditions
- `test_rate_limiting.py`: Test rate limiting with different scenarios

#### 5. **Command-Line Interface**
```bash
python server.py <directory> [OPTIONS]

Options:
  --single-threaded    # Run without threading
  --delay SECONDS      # Artificial delay
  --unsafe-counter     # Demonstrate race conditions
  --race-demo          # Force race conditions with delays
```

## Comparison

| Feature | Your Implementation | Victoria's Implementation |
|---------|-------------------|------------------------|
| Threading Model | Thread-per-request (optional) | Thread-per-request (always) |
| Counter Safety | Configurable (safe/unsafe) | Always safe with demo delay |
| Rate Limiting | 5 req/s, thread-safe | 5 req/s, thread-safe |
| Testing | 3 separate test scripts | 1 unified test script |
| Modes | Single & Multi-threaded | Multi-threaded only |
| CLI Flags | Extensive | Basic |
| Docker | Not included | Full Docker setup |
| Documentation | Comprehensive README | Comprehensive README with screenshots |
| Artificial Delay | Configurable | Fixed 0.5s |

## Key Similarities

1. **Thread Safety**: Both use locks for counter and rate limiter
2. **Rate Limiting Algorithm**: Identical sliding window approach
3. **HTTP Responses**: Both return proper 429 status codes
4. **Testing Approach**: Both test performance, race conditions, and rate limiting
5. **Directory Listing**: Both show hit counters in HTML table

## Key Differences

1. **Flexibility**: Your implementation offers more modes (single/multi-threaded, safe/unsafe counter)
2. **Docker**: Victoria has full Docker/compose setup, you don't
3. **Testing Scripts**: You have 3 separate focused scripts, Victoria has 1 comprehensive script
4. **UI/Styling**: Victoria has custom pink theme, you have standard table
5. **Port**: Victoria uses 8001, you use 8080

## Recommendations to Match Colleague's Work

### Already Matching:
✅ Multithreaded server with thread-per-request
✅ Thread-safe hit counter with locks
✅ IP-based rate limiting (5 req/s)
✅ Race condition demonstration
✅ Comprehensive testing scripts
✅ Detailed README documentation

### Could Add (Optional):
1. **Docker Support**: Add Dockerfile and docker-compose.yml
2. **Custom Styling**: Add custom theme to HTML (your choice of colors/fonts)
3. **Unified Test Script**: Combine test scripts or keep them separate (both valid)
4. **Fixed Artificial Delay**: Your configurable approach is actually better
5. **Screenshots**: Add visual documentation of results

## Conclusion

Both implementations successfully complete the lab requirements:
- ✅ Multithreaded server
- ✅ Concurrent request handling
- ✅ Hit counter with race condition demo
- ✅ Thread-safe counter with locks
- ✅ Rate limiting (5 req/s per IP)
- ✅ Comprehensive testing
- ✅ Documentation

Your implementation offers **more flexibility and configuration options**, while Victoria's implementation includes **Docker deployment** and **custom UI styling**. Both are excellent solutions to the lab requirements!
