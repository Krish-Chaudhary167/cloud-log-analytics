import sys

current, users = None, set()

for line in sys.stdin:
    key, user = line.rstrip("\n").split("\t")
    if key == current:
        users.add(user)
    else:
        if current is not None:
            print(f"{current}\t{len(users)}")
        current, users = key, {user}

if current is not None:
    print(f"{current}\t{len(users)}")