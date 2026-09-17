# Summary: Fix for "deleting a nonexistent todo reports success"

## Investigation
`delete_todo()` in `app.py` correctly returned `204 No Content` when a todo was
found and deleted, but when the id did not exist it fell through to:

    return jsonify(error="todo not found"), 200

The JSON error body was there, but the HTTP status was **200 OK** — a success
code. Any client (curl, fetch, mobile apps) that checks the status code sees a
successful delete of something that was never deleted. This matched the user
reports exactly.

## Fix
Changed the not-found branch of `delete_todo()` to return the proper error
status:

    return jsonify(error="todo not found"), 404

A one-character-class change (`200` → `404`); no other behavior was touched.

## Verification
- Added `test_app.py` with a regression suite (8 tests) covering:
  - deleting a nonexistent todo returns 404 with an error body (the bug)
  - a generic check that deleting a missing todo never yields a 2xx status
  - deleting an existing todo still returns 204 and actually removes it
  - only the targeted todo is removed; deleting the same id twice gives
    204 then 404
  - GET endpoints still behave correctly (200 / 404)
- All 10 tests pass (including the original failing reproduction test).
- Live-server smoke test via HTTP:
  - `DELETE /todos/1` (exists)          → 204 No Content
  - `DELETE /todos/1` (now gone)        → 404 + `{"error":"todo not found"}`
  - `DELETE /todos/99` (never existed)  → 404 + `{"error":"todo not found"}`

## Result
The fix works: deleting a todo that does not exist now reports a 404 error
instead of success, while normal deletes are unaffected.
