import os
import subprocess
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=8000)
db = client[os.getenv("MONGO_DB", "log_analytics")]


def read_hdfs(job):
    """Read a MapReduce job's output from HDFS, split into columns."""
    result = subprocess.run(
        f"hdfs dfs -cat /output/{job}/part-*",
        shell=True, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Could not read /output/{job}: {result.stderr}")
    return [line.split("\t") for line in result.stdout.splitlines() if line.strip()]


def load(collection, docs):
    db[collection].delete_many({})          # clear old results so reruns don't duplicate
    if docs:
        db[collection].insert_many(docs)
    print(f"{collection}: {len(docs)} documents loaded")


# 1. Requests per endpoint
rows = read_hdfs("requests_per_endpoint")
load("requests_per_endpoint", [{"endpoint": r[0], "count": int(r[1])} for r in rows])

# 2. Errors per hour (plus an error rate percentage for the dashboard)
rows = read_hdfs("errors_per_hour")
docs = []
for r in rows:
    total, errors = int(r[1]), int(r[2])
    docs.append({"hour": r[0], "total": total, "errors": errors,
                 "error_rate": round(errors / total * 100, 2)})
load("errors_per_hour", docs)

# 3. Daily active users
rows = read_hdfs("daily_active_users")
load("daily_active_users", [{"date": r[0], "users": int(r[1])} for r in rows])

# 4. Security anomalies
rows = read_hdfs("anomalies")
load("anomalies", [{"ip": r[0], "failed_attempts": int(r[1])} for r in rows])

# Remember when the last load happened (the dashboard can show this)
db["meta"].replace_one(
    {"_id": "last_run"},
    {"_id": "last_run", "loaded_at": datetime.now(timezone.utc)},
    upsert=True,
)
print("Done.")
