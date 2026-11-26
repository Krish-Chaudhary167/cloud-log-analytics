import subprocess
import sys

job = sys.argv[1]                                   # e.g. anomalies
logfile = sys.argv[2] if len(sys.argv) > 2 else "logs/sample.log"


def run(script, data):
    p = subprocess.run([sys.executable, script], input=data,
                       capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        print(p.stderr)
        sys.exit(1)
    return p.stdout


data = open(logfile, encoding="utf-8").read()

mapped = run(f"mapreduce/{job}/mapper.py", data)                 # 1. MAP
shuffled = "\n".join(sorted(mapped.splitlines())) + "\n"         # 2. SHUFFLE & SORT
result = run(f"mapreduce/{job}/reducer.py", shuffled)            # 3. REDUCE

print(result)