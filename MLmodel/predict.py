import time
import json
import mimetypes
import os
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import joblib


MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(MODEL_DIR)
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
MODEL_PATH = os.path.join(MODEL_DIR, "credit_model.joblib")

MODEL = joblib.load(MODEL_PATH)
REQUIRED_FIELDS = [
    "mothly_income",
    "monthly_debt_payments",
    "dti_ratio",
    "late_payments_12m",
    "loan_amount",
    "loan_term_months",
]

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request processing time in seconds",
    ["method", "endpoint"],
)

def predict_default(payload):
    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    values = []
    for field in REQUIRED_FIELDS:
        try:
            values.append(float(payload[field]))
        except (TypeError, ValueError):
            raise ValueError(f"Field '{field}' must be numeric.")

    prediction = int(MODEL.predict([values])[0])
    return {"prediction": prediction, "default": bool(prediction)}


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/metrics":
            body = generate_latest()
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed_path.path == "/":
            self.serve_file(os.path.join(FRONTEND_DIR, "index.html"))
            return

        safe_path = os.path.normpath(parsed_path.path.lstrip("/"))
        file_path = os.path.join(FRONTEND_DIR, safe_path)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.serve_file(file_path)
            return

        self.send_error(404, "Not found")

    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path != "/api/predict":
            self.send_error(404, "Not found")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8") or "{}")
            result = predict_default(payload)
            self.send_json(200, result)
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body."})
        except ValueError as exc:
            self.send_json(400, {"error": str(exc)})
        except Exception as exc:  # pragma: no cover - defensive error handling
            self.send_json(500, {"error": f"Server error: {exc}"})

    def serve_file(self, file_path):
        try:
            with open(file_path, "rb") as file:
                content = file.read()
        except OSError:
            self.send_error(404, "Not found")
            return

        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = "application/octet-stream"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), RequestHandler)
    print(f"Credit model app is running on http://{host}:{port}")
    server.serve_forever()