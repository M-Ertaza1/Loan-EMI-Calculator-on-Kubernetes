import sys, os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

base = sys.argv[1] if len(sys.argv) > 1 else "."
res = os.path.join(base, "results")
out = os.path.join(res, "graphs")
os.makedirs(out, exist_ok=True)

# ---------- Graph 1: avg response time vs request rate ----------
s = pd.read_csv(os.path.join(res, "summary.csv"))
plt.figure(figsize=(7, 4.5))
for n, g in s.groupby("replicas"):
    g = g.sort_values("target_rps")
    plt.plot(g.target_rps, g.avg_response_ms, marker="o", label=f"{n} replica(s)")
plt.xscale("log"); plt.yscale("log")
rates = sorted(s.target_rps.unique())
plt.xticks(rates, [str(r) for r in rates])
plt.xlabel("Request rate (req/s)")
plt.ylabel("Average response time (ms, log scale)")
plt.title("Graph 1: Response time vs request rate")
plt.grid(True, which="both", alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(out, "graph1_response_time.png"), dpi=200)
plt.close()

# ---------- Graph 2: per-pod CPU, 100 req/s, 3 replicas ----------
p = pd.read_csv(os.path.join(res, "runs", "3rep_100rps", "pods.csv"))
p = p[p.pod.str.startswith("emi-web")].copy()
p["cpu_m"] = pd.to_numeric(p.cpu_m, errors="coerce")
t0 = p.timestamp.min()
p["t"] = p.timestamp - t0
p["cpu_pct"] = p.cpu_m / 100 * 100   # % of the 100m CPU request
plt.figure(figsize=(7, 4.5))
for pod, g in p.groupby("pod"):
    plt.plot(g.t, g.cpu_pct, marker="o", label=pod[-5:])
plt.axhline(250 / 100 * 100, color="red", ls="--", lw=0.8, label="limit (250m)")
plt.xlabel("Time since start of run (s)")
plt.ylabel("CPU (% of 100m request)")
plt.title("Graph 2: Per-pod CPU, 100 req/s, 3 replicas")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(out, "graph2_pod_cpu.png"), dpi=200)
plt.close()

# ---------- Graph 3: autoscaling ----------
a = os.path.join(res, "autoscale")
h = pd.read_csv(os.path.join(a, "hpa.csv"))
for c in h.columns:
    h[c] = pd.to_numeric(h[c], errors="coerce")
h = h.dropna(subset=["timestamp", "current_replicas"])
ph = pd.read_csv(os.path.join(a, "phases.csv"))
t0 = min(h.timestamp.min(), ph.timestamp.min())
h["t"] = (h.timestamp - t0) / 60
st = ph[ph.phase == "start"]
en = ph[ph.phase == "end"]
xs = list((st.timestamp - t0) / 60) + [(en.timestamp.max() - t0) / 60]
ys = list(st.rate) + [st.rate.iloc[-1]]

fig, ax = plt.subplots(3, 1, figsize=(8, 8), sharex=True)
ax[0].step(xs, ys, where="post", color="tab:blue")
ax[0].set_ylabel("Request rate (req/s)")
ax[0].set_title("Graph 3: Autoscaling test (10 -> 100 -> 10 req/s)")
hc = h.dropna(subset=["cpu_percent"])
ax[1].plot(hc.t, hc.cpu_percent, marker="o", color="tab:orange")
ax[1].axhline(50, color="red", ls="--", lw=0.8, label="HPA target 50%")
ax[1].set_ylabel("Avg CPU utilization (%)")
ax[1].legend()
ax[2].step(h.t, h.current_replicas, where="post", color="tab:green")
ax[2].set_ylabel("Web replicas")
ax[2].set_yticks([1, 2, 3, 4, 5])
ax[2].set_xlabel("Time (minutes since start of recording)")
for x in ax:
    x.grid(True, alpha=0.3)
fig.text(0.5, 0.005,
         "Scale-down to 1 replica was observed at about 08:00 (after the 5-min HPA stabilization window), "
         "after the recorded window ended.",
         ha="center", fontsize=7)
plt.tight_layout(rect=[0, 0.02, 1, 1])
plt.savefig(os.path.join(out, "graph3_autoscale.png"), dpi=200)
plt.close()

print("Saved graphs in", out)