import os
import redis
import time
from flask import Flask, request, jsonify

# Import prometheus client to export prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True,
)

# Prometheus metrics
redis_app_cache_hit = Counter(
    "redis_app_cache_hit",
    "Number of cache hits when getting items from Redis",
    ["key"],
)

request_count = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)


def instrument_endpoint(func):
    """Decorator to instrument endpoints with request counting and duration tracking"""

    def wrapper(*args, **kwargs):
        start_time = time.time()
        method = request.method
        endpoint = request.endpoint or func.__name__

        try:
            response = func(*args, **kwargs)
            status_code = 200
            if isinstance(response, tuple):
                status_code = response[1] if len(response) > 1 else 200

            # Record metrics
            request_count.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).inc()
            request_duration.labels(method=method, endpoint=endpoint).observe(
                time.time() - start_time
            )

            return response
        except Exception as e:
            # Record error metrics
            status_code = 500
            request_count.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).inc()
            request_duration.labels(method=method, endpoint=endpoint).observe(
                time.time() - start_time
            )
            raise e

    wrapper.__name__ = func.__name__
    return wrapper


@app.get("/")
@instrument_endpoint
def hello():
    return {"message": "Hello from Redis Flask App in Docker!"}


@app.post("/items")
@instrument_endpoint
def add_item():
    try:
        data = request.get_json()
        if not data or "key" not in data or "value" not in data:
            return jsonify({"error": "Missing key or value"}), 400

        key = data["key"]
        value = data["value"]

        redis_client.set(key, value)

        return (
            jsonify({"message": "Item added successfully", "key": key, "value": value}),
            201,
        )

    except redis.ConnectionError:
        return jsonify({"error": "Cannot connect to Redis"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/items/<key>")
@instrument_endpoint
def get_item(key):
    try:
        value = redis_client.get(key)
        if value is None:
            return jsonify({"error": "Key not found"}), 404

        # Increment cache hit counter
        redis_app_cache_hit.labels(key=key).inc()
        return jsonify({"key": key, "value": value})

    except redis.ConnectionError:
        return jsonify({"error": "Cannot connect to Redis"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/items")
@instrument_endpoint
def list_items():
    try:
        keys = redis_client.keys("*")
        items = {}
        for key in keys:
            value = redis_client.get(key)
            items[key] = value

        return jsonify({"count": len(items), "items": items})

    except redis.ConnectionError:
        return jsonify({"error": "Cannot connect to Redis"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/metrics")
@instrument_endpoint
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_BIND_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", 5000)),
        debug=True,
    )
