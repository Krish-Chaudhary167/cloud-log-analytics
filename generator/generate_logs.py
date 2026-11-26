import random
import argparse
import os
from datetime import datetime, timedelta

ENDPOINTS = ["/home", "/login", "/search", "/products", "/cart", "/checkout", "/profile", "/api/data"]
USERS = [f"user{i}" for i in range(1, 51)]                    # 50 users
NORMAL_IPS = [f"192.168.1.{i}" for i in range(10, 60)]       # normal IPs
ATTACKER_IPS = ["45.33.12.8", "103.77.4.21", "185.220.9.5"]  # suspicious IPs


def make_log(ts):
    # ~4% of traffic = attackers trying to brute-force /login
    if random.random() < 0.04:
        ip = random.choice(ATTACKER_IPS)
        user, endpoint, method, status = "guest", "/login", "POST", 401
    else:
        ip = random.choice(NORMAL_IPS)
        user = random.choice(USERS)
        endpoint = random.choice(ENDPOINTS)
        method = "POST" if endpoint in ("/login", "/checkout") else "GET"
        # error spike between 2 PM and 4 PM, otherwise few errors
        error_chance = 0.25 if 14 <= ts.hour < 16 else 0.05
        if random.random() < error_chance:
            status = random.choice([404, 500, 503])
        else:
            status = 200

    # errors are slower than successful requests
    response_time = random.randint(20, 400) if status == 200 else random.randint(400, 2000)
    return (ts, f"{ts:%Y-%m-%d %H:%M:%S},{user},{ip},{endpoint},{method},{status},{response_time}")


def generate(count, days):
    start = datetime.now() - timedelta(days=days)
    logs = []
    for _ in range(count):
        ts = start + timedelta(seconds=random.randint(0, days * 86400))
        logs.append(make_log(ts))
    logs.sort(key=lambda x: x[0])          # order by time
    return [line for _, line in logs]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=5000)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--out", default="logs/sample.log")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    lines = generate(args.count, args.days)
    with open(args.out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {len(lines)} log lines to {args.out}")