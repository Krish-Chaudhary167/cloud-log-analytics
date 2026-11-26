import os
import uuid
from datetime import datetime

import boto3
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()  # reads AWS keys and bucket name from .env

app = Flask(__name__)
BUCKET = os.getenv("S3_BUCKET")
s3 = boto3.client("s3", region_name=os.getenv("AWS_DEFAULT_REGION", "ap-south-1"))


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/logs", methods=["POST"])
def receive_logs():
    data = request.get_json(silent=True)
    if not data or not isinstance(data.get("logs"), list) or not data["logs"]:
        return jsonify(error='send JSON like {"logs": ["line1", "line2"]}'), 400

    lines = data["logs"]
    now = datetime.utcnow()
    key = f"logs/{now:%Y-%m-%d}/batch-{now:%H%M%S}-{uuid.uuid4().hex[:6]}.log"

    s3.put_object(Bucket=BUCKET, Key=key, Body=("\n".join(lines) + "\n").encode())
    return jsonify(status="stored", lines=len(lines), s3_key=key), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)