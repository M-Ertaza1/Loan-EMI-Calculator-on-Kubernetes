import re, glob, os, csv
rows = []
for d in sorted(glob.glob("../results/runs/*rep_*rps")):
    m = re.match(r"(\d+)rep_(\d+)rps", os.path.basename(d))
    replies = 0; rt_sum = 0.0; err = 0; bad = 0; dur = 0.0
    for f in glob.glob(d + "/httperf_*.txt"):
        t = open(f).read()
        r = re.search(r"Total: connections \d+ requests \d+ replies (\d+) test-duration ([\d.]+)", t)
        rt = re.search(r"Reply time \[ms\]: response ([\d.]+)", t)
        e = re.search(r"Errors: total (\d+)", t)
        st = re.search(r"Reply status: 1xx=(\d+) 2xx=(\d+) 3xx=(\d+) 4xx=(\d+) 5xx=(\d+)", t)
        if r:
            n = int(r.group(1)); replies += n; dur = max(dur, float(r.group(2)))
            if rt: rt_sum += float(rt.group(1)) * n
        if e: err += int(e.group(1))
        if st: bad += int(st.group(4)) + int(st.group(5))
    avg = round(rt_sum / replies, 1) if replies else ""
    rows.append([m.group(1), m.group(2), avg, err, bad, replies, round(replies / dur, 1) if dur else ""])
with open("../results/summary.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["replicas", "target_rps", "avg_response_ms", "errors", "non2xx", "replies", "achieved_rps"])
    w.writerows(rows)
print(open("../results/summary.csv").read())
