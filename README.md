# DS-584 Assignment 4: Loan EMI Calculator on Kubernetes (Minikube)

A Loan EMI Calculator (Node.js/Express, HTML, jQuery, Bootstrap) that stores every calculation in a 3-member MongoDB replica set. It runs on a single-node Minikube cluster behind the NGINX Ingress controller, with load testing (httperf) and a Horizontal Pod Autoscaler.

## Repository layout

| Folder | Content |
|---|---|
| `app/` | Application source, Dockerfile, `.dockerignore` |
| `k8s/` | Kubernetes manifests (numbered in apply order) |
| `scripts/` | Load-testing, profiling and helper scripts |
| `results/` | Raw outputs: `summary.csv`, per-run httperf/CPU logs, autoscale data, graphs, evidence |

## Prerequisites

Docker, Minikube, kubectl, and (for load tests) `httperf`, `jq`, Python 3.

## Bring up the whole system on a fresh Minikube cluster

```bash
# 1. Start the cluster and enable add-ons
minikube start --driver=docker --cpus=4 --memory=6144
minikube addons enable ingress
minikube addons enable metrics-server

# 2. Create the namespace
kubectl create namespace emi

# 3. Build the image and make it available inside the cluster
docker build -t emi-web:1.0 app/
minikube image load emi-web:1.0
minikube image load mongo:7        # optional: pre-load to avoid slow pulls

# 4. Deploy MongoDB first, wait for the pods, then everything else
kubectl apply -f k8s/00-mongo.yaml
kubectl wait --for=condition=ready pod/mongo-2 -n emi --timeout=300s
kubectl apply -f k8s/
```

`kubectl apply -f k8s/` applies the files in order: Mongo StatefulSet, `mongo-init` Job (runs `rs.initiate()`), ConfigMap, web Deployment and Service, Ingress, and the HPA (`05-hpa.yaml`). `05-hpa.yaml.disabled` is ignored by kubectl; it was used to keep the HPA out of the fixed-replica experiments.

### Verify

```bash
kubectl get all,pvc,configmap -n emi -o wide
kubectl logs job/mongo-init -n emi
kubectl exec -n emi mongo-0 -- mongosh --quiet --eval 'rs.status().members.map(m=>m.name+" "+m.stateStr)'
kubectl port-forward svc/emi-web 8080:80 -n emi      # then open http://localhost:8080
```

### Access through the Ingress

Linux (Docker driver):

```bash
echo "$(minikube ip) emi.local" | sudo tee -a /etc/hosts
```

Windows/macOS: run `minikube tunnel` and map `127.0.0.1 emi.local` in the hosts file. Then open http://emi.local.

## Application

- `POST /api/emi` with `{"principal":500000,"rate":12,"months":24}` returns EMI, total payment, total interest, `servedBy` (pod name) and `podIp`, and saves the calculation.
- `GET /api/history` returns the last 10 calculations.
- `GET /health` returns 200 only if MongoDB is reachable.
- Configuration: `MONGO_URL` environment variable (from ConfigMap `emi-config`).

## Experiments

```bash
cd scripts
./distribute.sh                 # 30 requests, count per pod
./loop.sh                       # continuous request loop (HTTP status per request)
./run_experiments.sh            # 15 runs: 1/2/3 replicas x 10,25,50,100,200 req/s, 60 s each
python3 summarize.py            # writes results/summary.csv
./run_autoscale.sh              # HPA test: 2 min 10 rps, 5 min 100 rps, 3 min 10 rps
```

Notes: httperf accepts at most 1000 sessions per session file, so `load.sh` splits each run into parallel httperf instances. `monitor.py` records host CPU every second and `kubectl top pods` every 15 s. Graphs are produced by `plot.py` (pandas, matplotlib) and saved in `results/graphs/`.

## Results summary

- 1 replica at 200 req/s saturates: 533 ms average, 3079 timeouts, 147 req/s achieved. With 2 or 3 replicas the same load is served without errors.
- HPA scaled 1 to 3 to 5 replicas when CPU reached 126% of the request, and returned to 1 replica after the 5-minute scale-down stabilization window.
- Web pod deletion, MongoDB PRIMARY deletion and a rolling update (1.0 to 1.1) produced no failed requests in the request loops.
