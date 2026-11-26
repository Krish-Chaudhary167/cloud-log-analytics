import sys

for line in sys.stdin:
    parts = line.strip().split(",")
    if len(parts) != 7:
        continue
    hour = parts[0][:13]                        # "2026-11-25 14"
    is_error = 1 if int(parts[5]) >= 400 else 0
    print(f"{hour}\t1,{is_error}")              # (1 request, error or not)