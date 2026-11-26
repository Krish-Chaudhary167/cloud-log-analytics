import sys
import time
import requests
from generate_logs import generate

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
BATCH = 500

lines = generate(5000, 7)
for i in range(0, len(lines), BATCH):
    r = requests.post(f"{API}/logs", json={"logs": lines[i:i + BATCH]})
    print(r.status_code, r.json())
    time.sleep(0.2)