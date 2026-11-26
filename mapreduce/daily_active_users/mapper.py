import sys

for line in sys.stdin:
    parts = line.strip().split(",")
    if len(parts) != 7:
        continue
    user = parts[1]
    if user == "guest":          # not-logged-in attackers aren't real users
        continue
    print(f"{parts[0][:10]}\t{user}")     # date, user