import sys

current, total, errors = None, 0, 0

for line in sys.stdin:
    key, val = line.rstrip("\n").split("\t")
    t, e = val.split(",")
    if key == current:
        total += int(t)
        errors += int(e)
    else:
        if current is not None:
            print(f"{current}\t{total}\t{errors}")
        current, total, errors = key, int(t), int(e)

if current is not None:
    print(f"{current}\t{total}\t{errors}")