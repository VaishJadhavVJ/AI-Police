# Rate Limiter Fix Summary

## Problem
Users reported that the rate limiter allowed one more request through than the configured limit (with `max_requests=2`, three requests were allowed).

## Root Cause
In `RateLimiter.allow()` (app.py), the limit check compared against the list of *previously recorded* requests, before the incoming request was counted:

```python
if len(self._requests) > self.max_requests:
    return False
```

At the moment the Nth+1 request arrives, the list still holds at most N entries, so `len > max_requests` is never true until an (N+2)th request arrives — by which point the (N+1)th has already been admitted. Result: `max_requests + 1` requests always got through.

## Fix
Changed the comparison to `>=`, so a request is rejected when the window already contains the maximum number of requests:

```python
if len(self._requests) >= self.max_requests:
    return False
```

One-character change; no other logic touched.

## Verification
Wrote a verification script (`/tmp/verify.py`) using an injectable fake clock. All checks pass:
1. `max_requests=2` → exactly `[True, True, False, False]` (was `[True, True, True, False]` before the fix).
2. `max_requests=1` → second request denied.
3. Window expiry → capacity restored after 60s; request at 59.9s still denied.
4. Boundary-age expiry → a timestamp exactly `window_seconds` old falls out of the window (consistent with the `now - timestamp < window_seconds` eviction rule).
5. End-to-end via Flask test client → `/check` returns `allowed=True, True, False`.

No pre-existing test suite in the workspace; `run_tests` reported no tests. The bug was reproduced before the fix and is gone after.
