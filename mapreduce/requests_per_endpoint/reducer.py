import sys

current, total = None, 0

for line in sys.stdin:
    key, val = line.rstrip("\n").split("\t")
    if key == current:
        total += int(val)
    else:
        if current is not None:
            print(f"{current}\t{total}")
        current, total = key, int(val)

if current is not None:          # don't forget the last key
    print(f"{current}\t{total}")