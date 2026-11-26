import sys

THRESHOLD = 20       # more than this many failures = suspicious
current, total = None, 0

def emit(ip, count):
    if count >= THRESHOLD:
        print(f"{ip}\t{count}")

for line in sys.stdin:
    key, val = line.rstrip("\n").split("\t")
    if key == current:
        total += int(val)
    else:
        if current is not None:
            emit(current, total)
        current, total = key, int(val)

if current is not None:
    emit(current, total)