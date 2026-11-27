import os
import uuid
from datetime import datetime, timezone

import boto3
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = Flask(__name__)

BUCKET = os.getenv("S3_BUCKET")
s3 = boto3.client("s3", region_name=os.getenv("AWS_DEFAULT_REGION", "ap-south-1"))

mongo = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
db = mongo[os.getenv("MONGO_DB", "log_analytics")]

DASHBOARD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboard"))


@app.route("/")
def dashboard():
    return send_from_directory(DASHBOARD_DIR, "index.html")


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/logs", methods=["POST"])
def receive_logs():
    data = request.get_json(silent=True)
    if not data or not isinstance(data.get("logs"), list) or not data["logs"]:
        return jsonify(error='send JSON like {"logs": ["line1", "line2"]}'), 400

    lines = data["logs"]
    now = datetime.now(timezone.utc)
    key = f"logs/{now:%Y-%m-%d}/batch-{now:%H%M%S}-{uuid.uuid4().hex[:6]}.log"
    s3.put_object(Bucket=BUCKET, Key=key, Body=("\n".join(lines) + "\n").encode())
    return jsonify(status="stored", lines=len(lines), s3_key=key), 201


def fetch(collection, sort_field=None):
    cursor = db[collection].find({}, {"_id": 0})
    if sort_field:
        cursor = cursor.sort(sort_field, 1)
    return list(cursor)


@app.route("/analytics")
def analytics():
    try:
        endpoints = sorted(fetch("requests_per_endpoint"), key=lambda e: e["count"], reverse=True)
        hourly = fetch("errors_per_hour", "hour")
        daily = fetch("daily_active_users", "date")
        anomalies = sorted(fetch("anomalies"), key=lambda a: a["failed_attempts"], reverse=True)
        meta = db["meta"].find_one({"_id": "last_run"})

        total_requests = sum(e["count"] for e in endpoints)
        total_errors = sum(h["errors"] for h in hourly)
        summary = {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": round(total_errors / total_requests * 100, 2) if total_requests else 0,
            "peak_daily_users": max((d["users"] for d in daily), default=0),
            "suspicious_ips": len(anomalies),
        }
        return jsonify(
            summary=summary,
            endpoints=endpoints,
            hourly=hourly,
            daily=daily,
            anomalies=anomalies,
            last_run=meta["loaded_at"].isoformat() if meta else None,
        )
    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
