"""Black-box route checks for the Express TODO app.

Run after starting the app and MongoDB with `docker compose up --build -d`.
Set APP_BASE_URL to test a different host or port.
"""

import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


BASE_URL = os.environ.get("APP_BASE_URL", "http://127.0.0.1:3000").rstrip("/")
TIMEOUT = 5


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect())


def request(method, path, form=None):
    body = urllib.parse.urlencode(form or {}).encode() if form is not None else None
    req = urllib.request.Request(
        BASE_URL + path,
        data=body,
        method=method,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with OPENER.open(req, timeout=TIMEOUT) as response:
            return response.status, response.headers, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, error.headers, error.read().decode("utf-8", "replace")


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def wait_until_ready():
    deadline = time.monotonic() + 90
    last_error = "no response"
    while time.monotonic() < deadline:
        try:
            status, _, body = request("GET", "/health")
            if status == 200:
                check('"status":"healthy"' in body, "GET /health reports healthy")
                return
            last_error = f"HTTP {status}: {body[:100]}"
        except Exception as error:  # retry while Docker Compose starts MongoDB and Node
            last_error = str(error)
        time.sleep(2)
    raise RuntimeError(f"App did not become ready at {BASE_URL}: {last_error}")


def main():
    wait_until_ready()

    status, _, home = request("GET", "/")
    check(status == 200, "GET / renders the task matrix")
    for quadrant in ("Do", "Schedule", "Delegate", "Eliminate"):
        check(quadrant in home, f"GET / includes the {quadrant} quadrant")

    status, _, form_page = request("GET", "/tasks/new")
    check(status == 200 and 'name="title"' in form_page, "GET /tasks/new renders the form")

    status, _, invalid_form = request("POST", "/tasks", {"title": "   "})
    check(status == 400 and "Title cannot be empty." in invalid_form,
          "POST /tasks rejects an empty title")

    title = f"PBL automation {uuid.uuid4().hex[:10]}"
    status, headers, _ = request(
        "POST",
        "/tasks",
        {"title": title, "description": "Created by the route test", "isUrgent": "on", "isImportant": "on"},
    )
    check(status == 303 and headers.get("Location") == "/", "POST /tasks creates and redirects")

    status, _, home = request("GET", "/")
    check(status == 200 and title in home, "GET / displays the newly created task")
    match = re.search(r'action="/tasks/([0-9a-f]{24})/delete"', home)
    check(match is not None, "GET / exposes the task delete route")
    task_id = match.group(1)

    status, _, _ = request("POST", "/tasks/not-an-object-id/delete")
    check(status == 400, "POST /tasks/:id/delete rejects malformed IDs")
    status, _, _ = request("POST", "/tasks/000000000000000000000000/delete")
    check(status == 404, "POST /tasks/:id/delete returns 404 for a missing task")
    status, headers, _ = request("POST", f"/tasks/{task_id}/delete")
    check(status == 303 and headers.get("Location") == "/",
          "POST /tasks/:id/delete removes the task and redirects")

    status, _, home = request("GET", "/")
    check(status == 200 and title not in home, "GET / confirms the task was removed")

    status, _, _ = request("GET", "/tasks")
    check(status == 404, "GET /tasks is not an unintended route")
    status, _, _ = request("GET", f"/tasks/{task_id}/delete")
    check(status == 404, "GET /tasks/:id/delete is not allowed")

    print("All route checks passed.")


if __name__ == "__main__":
    main()
