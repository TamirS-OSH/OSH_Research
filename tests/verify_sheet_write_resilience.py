"""Verify the Google Sheets write survives transient API failures.

Exercises the retry/backoff helper and the write ordering in
dashboard/scraper.py against a fake gspread client. No network, no credentials
and no real sleeping: google.auth.default, gspread.authorize and time.sleep are
all stubbed out.

    python tests/verify_sheet_write_resilience.py

The properties under test are the two that the 2026-08-16 crash exposed:

  1. A transient 503 on any of the sheet calls is retried, not fatal.
  2. The sheet is never emptied. The old code ran clear() then update(), so a
     failure between them left the dashboard blank; the new code overwrites in
     place and only then clears whatever trailed the new final row.

Exit code 0 means every check passed. Any failure prints the mismatch and
exits 1.
"""

import pathlib
import sys

import pandas as pd
from gspread.exceptions import APIError

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "dashboard"))
import scraper  # noqa: E402

COLUMNS = ["Subject Domain", "Journal Name", "Article Title",
           "Publication Date", "Grade", "Citations", "Article Link"]

failures = []


def check(label, actual, expected):
    if actual != expected:
        failures.append(f"{label}\n     expected: {expected!r}\n     actual:   {actual!r}")
        print(f"  FAIL {label}")
    else:
        print(f"  ok   {label}")


class FakeResponse:
    """A response whose body is not JSON, as Google's 503 pages typically are.

    That combination is the point: it drives gspread's APIError.code to -1, so
    a retry decision based on .code alone would misread it as non-transient.
    """

    def __init__(self, status_code, body="<html>Service unavailable</html>", headers=None):
        self.status_code = status_code
        self.text = body
        self.headers = headers or {}

    def json(self):
        raise ValueError("not JSON")


class JsonErrorResponse(FakeResponse):
    """A well-formed API error, e.g. a renamed spreadsheet."""

    def __init__(self, status_code, message):
        super().__init__(status_code, body=message)
        self._payload = {"error": {"code": status_code, "message": message,
                                   "status": "ERROR"}}

    def json(self):
        return self._payload


def api_error(status_code, message="boom", headers=None):
    if status_code in (429, 500, 502, 503, 504):
        return APIError(FakeResponse(status_code, headers=headers))
    return APIError(JsonErrorResponse(status_code, message))


class FakeSheet:
    """Records every mutating call in order, and can fail the first N writes."""

    def __init__(self, rows, cols, failed_writes=0):
        self.row_count = rows
        self.col_count = cols
        self.calls = []
        self._failed_writes = failed_writes

    def resize(self, rows=None, cols=None):
        self.calls.append(("resize", rows, cols))
        self.row_count, self.col_count = rows, cols

    def update(self, values, range_name=None):
        if self._failed_writes > 0:
            self._failed_writes -= 1
            self.calls.append(("update-503", len(values)))
            raise api_error(503)
        self.calls.append(("update", len(values)))

    def batch_clear(self, ranges):
        self.calls.append(("batch_clear", tuple(ranges)))

    def clear(self):
        # The call that must never happen: it is what could empty the dashboard.
        self.calls.append(("clear",))


def install_fakes(sheet, open_errors=()):
    """Point scraper at `sheet`, optionally failing the first opens."""
    pending = list(open_errors)

    class FakeSpreadsheet:
        sheet1 = sheet

    class FakeClient:
        def open(self, title, folder_id=None):
            if pending:
                raise pending.pop(0)
            return FakeSpreadsheet()

    scraper.google.auth.default = lambda scopes=None: (object(), "fake-project")
    scraper.gspread.authorize = lambda credentials: FakeClient()


def frame(rows):
    return pd.DataFrame(
        [[f"v{i}"] * len(COLUMNS) for i in range(rows)], columns=COLUMNS)


# time.sleep is the only thing that would make this slow; record the waits
# instead of taking them, so the backoff schedule itself is assertable.
waits = []
scraper.time.sleep = waits.append


print("retry_reason classification")
check("503 with a non-JSON body is transient",
      scraper.retry_reason(api_error(503)), "HTTP 503")
check("429 is transient", scraper.retry_reason(api_error(429)), "HTTP 429")
check("404 is not transient", scraper.retry_reason(api_error(404)), None)
check("403 is not transient", scraper.retry_reason(api_error(403)), None)
check("connection error is transient",
      scraper.retry_reason(scraper.requests.exceptions.ConnectionError()),
      "connection error")
check("timeout is transient",
      scraper.retry_reason(scraper.requests.exceptions.Timeout()),
      "connection error")

print("\nwith_retry control flow")
attempts = []


def flaky():
    attempts.append(1)
    if len(attempts) < 3:
        raise api_error(503)
    return "done"


waits.clear()
check("succeeds after two 503s", scraper.with_retry("flaky", flaky), "done")
check("took exactly three attempts", len(attempts), 3)
check("backoff doubled between retries", waits, [5, 10])

waits.clear()
permanent = []


def renamed_sheet():
    permanent.append(1)
    raise api_error(404, "Requested entity was not found.")


try:
    scraper.with_retry("permanent", renamed_sheet)
except APIError as e:
    check("non-transient error propagates", e.response.status_code, 404)
else:
    failures.append("a 404 should have propagated out of with_retry")
check("non-transient error was not retried", len(permanent), 1)
check("non-transient error did not sleep", waits, [])

waits.clear()
always = []


def always_503():
    always.append(1)
    raise api_error(503)


try:
    scraper.with_retry("always", always_503, max_retries=4)
except APIError as e:
    check("exhausted retries re-raise the last error", e.response.status_code, 503)
else:
    failures.append("exhausting retries should re-raise")
check("stopped at max_retries attempts", len(always), 4)
check("slept between each attempt but not after the last", waits, [5, 10, 20])

waits.clear()
throttled = []


def rate_limited_once():
    throttled.append(1)
    if len(throttled) == 1:
        raise api_error(429, headers={"Retry-After": "42"})
    return "ok"


scraper.with_retry("retry-after", rate_limited_once)
check("Retry-After header overrides the backoff", waits, [42])

print("\nupload ordering: grid taller than the new data")
sheet = FakeSheet(rows=1000, cols=7)
install_fakes(sheet)
scraper.update_google_sheet(frame(100))
check("no resize needed",
      [c for c in sheet.calls if c[0] == "resize"], [])
check("wrote 101 rows then cleared only the trailing range",
      sheet.calls,
      [("update", 101), ("batch_clear", ("A102:G1000",))])
check("clear() was never called", [c for c in sheet.calls if c[0] == "clear"], [])

print("\nupload ordering: new data taller than the grid")
sheet = FakeSheet(rows=50, cols=7)
install_fakes(sheet)
scraper.update_google_sheet(frame(100))
check("grew the grid before writing, and cleared nothing after",
      sheet.calls,
      [("resize", 101, 7), ("update", 101)])

print("\nupload ordering: transient failures on open and write")
waits.clear()
sheet = FakeSheet(rows=1000, cols=7, failed_writes=2)
install_fakes(sheet, open_errors=[api_error(503), api_error(503)])
scraper.update_google_sheet(frame(100))
check("the write was retried and the cleanup still ran",
      sheet.calls,
      [("update-503", 101), ("update-503", 101), ("update", 101),
       ("batch_clear", ("A102:G1000",))])
check("clear() was never called", [c for c in sheet.calls if c[0] == "clear"], [])
check("slept for two open retries and two write retries", waits, [5, 10, 5, 10])

print()
if failures:
    print(f"FAILED ({len(failures)} check(s)):\n")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("All checks passed.")
