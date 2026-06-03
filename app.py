from flask import Flask, jsonify
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import os, time

app = Flask(__name__)

REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'Request duration', ['method', 'endpoint'])

@app.before_request
def start_timer():
    from flask import request
    request._start = time.time()

@app.after_request
def record_metrics(response):
    from flask import request
    dur = time.time() - request._start
    REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
    REQUEST_DURATION.labels(request.method, request.path).observe(dur)
    return response

@app.route('/')
def hello():
    return "Hello, Ops!"

@app.route('/health')
def health():
    return jsonify({"status": "ok", "hostname": os.uname().nodename})

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
