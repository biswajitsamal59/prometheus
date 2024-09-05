from flask import Flask, Blueprint, request
import random
import time
from prometheus_client import Counter, Summary, generate_latest  # Import generate_latest here
import resource_user as eater

app = Flask(__name__)

res_bp = Blueprint("resource_user", __name__, url_prefix="/resource_user")

# Define Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total number of HTTP requests', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Summary('http_request_latency_seconds', 'Latency of HTTP requests in seconds', ['method', 'endpoint'])
EXCEPTIONS_COUNT = Counter('exceptions_total', 'Total number of exceptions raised', ['exception_type'])

@app.before_request
def start_timer():
    request.start_time = time.time()

@app.after_request
def record_request_data(response):
    latency = time.time() - request.start_time
    REQUEST_LATENCY.labels(request.method, request.path).observe(latency)
    REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
    return response

@app.teardown_request
def handle_exception(error=None):
    if error:
        EXCEPTIONS_COUNT.labels(type(error).__name__).inc()

@app.route("/metrics")
def metrics():
    return generate_latest()


@app.route("/random_client_side_error")
def rcse():
    return {"status": "client_failure"}, random.randrange(400, 418)


@app.route("/random_server_side_error")
def rsse():
    return {"status": "server_failure"}, random.randrange(500, 508)


@app.route("/unhandled_exception")
def ue():
    raise Exception("Unhandled exception!")


@res_bp.route("/high_cpu_low_mem")
def hclm():
    n = request.args.get("n", type=int, default=1)
    result = eater.high_cpu_low_mem(n)
    return {"n": n, "result": result}


@res_bp.route("/high_cpu_high_mem")
def hchm():
    n = request.args.get("n", type=int, default=1)
    result = eater.high_cpu_high_mem(n)
    return {"n": n, "result": result}


@res_bp.route("/low_cpu_low_mem")
def lclm():
    n = request.args.get("n", type=int, default=1)
    result = eater.low_cpu_low_mem(n)
    return {"n": n, "result": result}


@res_bp.route("/med_cpu_high_mem")
def mchm():
    n = request.args.get("n", type=int, default=1)
    result = eater.med_cpu_high_mem(n)
    return {"n": n, "result": result}


app.register_blueprint(res_bp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


# TODO
# create load-testing mechanism/script
# Create endpoints to return error codes (server side + client side), throw unhandled exceptions, intentionally have high latency
# Specify cpu+memory resources allocated to each pod
# Add README and describe exact process of how to run this app and see metrics in Site24x7