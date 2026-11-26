import sys

for line in sys.stdin:
    parts = line.strip().split(",")
    if len(parts) != 7:
        continue
    if parts[5] == "401":                # failed login / unauthorized
        print(f"{parts[2]}\t1")          # ip, 1