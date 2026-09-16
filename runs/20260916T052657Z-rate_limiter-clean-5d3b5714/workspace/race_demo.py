"""Deterministic proof of the check-then-act race in RateLimiter.allow().

Uses a per-thread sys.settrace hook to stall a thread on the
`self._requests.append(now)` line -- i.e., *after* its length check has
already passed but *before* it records the request. This is exactly the
bytecode-level interleaving an OS preemption can produce under a threaded
WSGI server. Against a properly locked implementation this is harmless;
against the unsynchronized one it admits more requests than allowed.
"""
import linecache
import sys
import threading

from app import RateLimiter

# Locate the append line inside RateLimiter.allow.
_APPEND_LINE = None
_code = RateLimiter.allow.__code__
for _ln in range(_code.co_firstlineno, _code.co_firstlineno + 25):
    if "append" in linecache.getline("app.py", _ln):
        _APPEND_LINE = _ln
        break
assert _APPEND_LINE, "could not locate append line in app.py"


def run_once(n_threads=6, max_requests=3):
    limiter = RateLimiter(max_requests=max_requests, window_seconds=60)
    barrier = threading.Barrier(n_threads)
    results = []
    lock = threading.Lock()

    def worker():
        barrier.wait()
        stalled = False

        def trace(frame, event, arg):
            nonlocal stalled
            if event == "line" and frame.f_lineno == _APPEND_LINE and not stalled:
                stalled = True
                import time
                time.sleep(0.01)  # simulate preemption mid-critical-section
            return trace

        sys.settrace(trace)
        try:
            allowed = limiter.allow()
        finally:
            sys.settrace(None)
        with lock:
            results.append(allowed)

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return sum(results)


if __name__ == "__main__":
    rounds = [run_once() for _ in range(3)]
    print("admitted per round (limit is 3):", rounds)
    if any(r > 3 for r in rounds):
        print("RACE CONFIRMED: limit exceeded with concurrent allow() calls")
    else:
        print("no violation observed this run")
