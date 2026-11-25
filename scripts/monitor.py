import sys, os, time, threading, subprocess
out = sys.argv[1]; want_hpa = "--hpa" in sys.argv
os.makedirs(out, exist_ok=True)
stop = False

def cpu_times():
    v = list(map(int, open("/proc/stat").readline().split()[1:]))
    return sum(v), v[3] + v[4]          # total, idle+iowait

def host():
    with open(os.path.join(out, "host_cpu.csv"), "w") as f:
        f.write("timestamp,cpu_percent\n")
        t0, i0 = cpu_times()
        while not stop:
            time.sleep(1)
            t1, i1 = cpu_times()
            pct = 100.0 * (1 - (i1 - i0) / max(t1 - t0, 1))
            f.write("%.0f,%.1f\n" % (time.time(), pct)); f.flush()
            t0, i0 = t1, i1

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout

def pods():
    with open(os.path.join(out, "pods.csv"), "w") as f:
        f.write("timestamp,pod,cpu_m,mem_Mi\n")
        while not stop:
            ts = "%.0f" % time.time()
            try:
                for line in run(["kubectl", "top", "pods", "-n", "emi", "--no-headers"]).splitlines():
                    p = line.split()
                    if len(p) >= 3:
                        f.write("%s,%s,%s,%s\n" % (ts, p[0], p[1].rstrip("m"), p[2].rstrip("Mi")))
                f.flush()
            except Exception as e:
                pass
            time.sleep(15)

def hpa():
    with open(os.path.join(out, "hpa.csv"), "w") as f, open(os.path.join(out, "hpa_raw.txt"), "w") as raw:
        f.write("timestamp,current_replicas,desired_replicas,cpu_percent\n")
        while not stop:
            ts = "%.0f" % time.time()
            try:
                j = run(["kubectl", "get", "hpa", "emi-web", "-n", "emi", "-o",
                         "jsonpath={.status.currentReplicas},{.status.desiredReplicas},{.status.currentMetrics[0].resource.current.averageUtilization}"])
                f.write("%s,%s\n" % (ts, j)); f.flush()
                raw.write("%s %s\n" % (time.strftime("%T"), run(["kubectl", "get", "hpa", "emi-web", "-n", "emi", "--no-headers"]).strip())); raw.flush()
            except Exception:
                pass
            time.sleep(15)

ths = [threading.Thread(target=host, daemon=True), threading.Thread(target=pods, daemon=True)]
if want_hpa: ths.append(threading.Thread(target=hpa, daemon=True))
for t in ths: t.start()
try:
    while True: time.sleep(1)
except KeyboardInterrupt:
    stop = True
