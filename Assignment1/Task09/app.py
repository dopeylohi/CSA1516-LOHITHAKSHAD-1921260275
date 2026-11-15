#!/usr/bin/env python3
"""Smart Campus PoC: tiny university REST API (standard library only, DUMMY data)."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

RESULTS = {
    "S1001": {"name": "Sample Student A", "semester": 2, "gpa": 8.4},
    "S1002": {"name": "Sample Student B", "semester": 2, "gpa": 7.9},
}
FEES = {
    "S1001": {"due": 45000, "paid": 0},
    "S1002": {"due": 45000, "paid": 45000},
}
BOOKS = [
    {"id": 1, "title": "Operating System Concepts", "available": True},
    {"id": 2, "title": "Cloud Computing Principles", "available": False},
    {"id": 3, "title": "Computer Networks", "available": True},
]


class Handler(BaseHTTPRequestHandler):
    def send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        parts = [p for p in url.path.split("/") if p]
        if parts == ["health"]:
            return self.send_json(200, {"status": "ok"})
        if len(parts) == 3 and parts[:2] == ["api", "results"]:
            r = RESULTS.get(parts[2])
            if r is None:
                return self.send_json(404, {"error": "student not found"})
            return self.send_json(200, dict(regno=parts[2], **r))
        if len(parts) == 3 and parts[:2] == ["api", "fees"]:
            f = FEES.get(parts[2])
            if f is None:
                return self.send_json(404, {"error": "student not found"})
            return self.send_json(200, dict(regno=parts[2], balance=f["due"] - f["paid"], **f))
        if parts == ["api", "library", "search"]:
            q = parse_qs(url.query).get("q", [""])[0].lower()
            return self.send_json(200, {"query": q, "results": [b for b in BOOKS if q in b["title"].lower()]})
        return self.send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/fees/pay":
            return self.send_json(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n))
            regno, amount = data["regno"], int(data["amount"])
        except (ValueError, KeyError, TypeError):
            return self.send_json(400, {"error": "need JSON with regno and integer amount"})
        f = FEES.get(regno)
        if f is None:
            return self.send_json(404, {"error": "student not found"})
        if amount <= 0 or amount > f["due"] - f["paid"]:
            return self.send_json(400, {"error": "invalid amount"})
        f["paid"] += amount
        return self.send_json(200, {"regno": regno, "status": "payment accepted", "balance": f["due"] - f["paid"]})


if __name__ == "__main__":
    print("University API listening on port 8000", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
