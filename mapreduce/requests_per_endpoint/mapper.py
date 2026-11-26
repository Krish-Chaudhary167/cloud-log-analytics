import sys

for line in sys.stdin:
    parts = line.strip().split(",")
    if len(parts) != 7:          # skip broken lines
        continue
    print(f"{parts[3]}\t1")      # endpoint, 1