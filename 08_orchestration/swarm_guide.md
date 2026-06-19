# 🐳 Module 08 — Orchestration Guide

> **Level:** 🔴 Advanced | **Time:** ~4 hours | **Prerequisites:** Modules 01-07

---

## 📖 Table of Contents

- [Orchestration Overview](#orchestration-overview)
- [Docker Swarm](#docker-swarm)
- [Swarm Networking](#swarm-networking)
- [Swarm Services & Scaling](#swarm-services--scaling)
- [Rolling Updates & Rollbacks](#rolling-updates--rollbacks)
- [Kubernetes Migration Path](#kubernetes-migration-path)

---

## Orchestration Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│              ORCHESTRATION COMPARISON                                │
├─────────────────┬────────────────────┬───────────────────────────────┤
│  Feature        │  Docker Swarm      │  Kubernetes                  │
├─────────────────┼────────────────────┼───────────────────────────────┤
│ Setup           │ Minutes            │ Hours/Days                    │
│ Learning curve  │ Low                │ High                          │
│ Multi-host      │ Yes                │ Yes                           │
│ Auto-scaling    │ Manual             │ HPA/VPA/KEDA                  │
│ Self-healing    │ Basic              │ Advanced                      │
│ Load balancing  │ Built-in (routing  │ Multiple options              │
│                 │ mesh)              │                               │
│ Storage         │ Volumes            │ PV/PVC/StorageClass           │
│ Networking      │ Overlay            │ CNI plugins                   │
│ Config/Secrets  │ Built-in           │ ConfigMap/Secret              │
│ Rolling updates │ Yes                │ Yes                           │
│ Rollbacks       │ Yes                │ Yes                           │
│ RBAC            │ Basic              │ Advanced                      │
│ Custom resources│ No                 │ Yes (CRDs)                    │
│ Ecosystem       │ Moderate           │ Huge                          │
│ Best for        │ Simple multi-host  │ Complex, large-scale          │
└─────────────────┴────────────────────┴───────────────────────────────┘

WHEN TO CHOOSE SWARM:
  ✅ Simpler operations (devs manage their own infra)
  ✅ Small-medium teams (<50 engineers)
  ✅ Already using Docker Compose (easy migration)
  ✅ Limited time to learn new tooling
  ✅ <50 containers / <10 hosts

WHEN TO CHOOSE KUBERNETES:
  ✅ Large-scale deployments (100s of services)
  ✅ Dedicated platform/infra teams
  ✅ Need fine-grained auto-scaling
  ✅ Advanced networking requirements (service mesh)
  ✅ Multi-cloud or hybrid deployments
```

---

## Docker Swarm

### Cluster Setup

```bash
# ── Initialize Swarm on manager node ─────────────────────────────────────────
docker swarm init --advertise-addr <MANAGER-IP>

# Output includes join token:
# docker swarm join --token SWMTKN-... <MANAGER-IP>:2377

# ── Get join tokens ───────────────────────────────────────────────────────────
docker swarm join-token worker    # Token for adding workers
docker swarm join-token manager   # Token for adding managers (HA)

# ── Add worker nodes (run on each worker) ─────────────────────────────────────
docker swarm join \
  --token SWMTKN-1-... \
  <MANAGER-IP>:2377

# ── Add manager nodes (for HA) ────────────────────────────────────────────────
# Recommended: 3 or 5 managers (odd number for Raft consensus)
docker swarm join \
  --token SWMTKN-1-...(manager-token)... \
  <MANAGER-IP>:2377

# ── Inspect cluster ───────────────────────────────────────────────────────────
docker node ls                    # List all nodes
docker node inspect <node-id>     # Node details
docker node promote <node-id>     # Worker → Manager
docker node demote <node-id>      # Manager → Worker

# ── Node labels (for placement constraints) ───────────────────────────────────
docker node update --label-add db=true <node-id>
docker node update --label-add zone=us-east-1a <node-id>
```

### Swarm Architecture

```
DOCKER SWARM CLUSTER (3 manager + 3 worker example)
──────────────────────────────────────────────────────────────────────

  ┌─────────────────────────────────────────────────────────────┐
  │                    MANAGER NODES                            │
  │                   (Raft consensus)                          │
  │  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
  │  │ Manager 1  │  │ Manager 2  │  │ Manager 3  │           │
  │  │ (Leader)   │  │ (Follower) │  │ (Follower) │           │
  │  │ Control    │  │ Standby    │  │ Standby    │           │
  │  └────────────┘  └────────────┘  └────────────┘           │
  └───────────────────────────────┬─────────────────────────────┘
                                  │ Schedule tasks
  ┌───────────────────────────────▼─────────────────────────────┐
  │                    WORKER NODES                             │
  │  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
  │  │  Worker 1  │  │  Worker 2  │  │  Worker 3  │           │
  │  │ app-rep-1  │  │ app-rep-2  │  │ app-rep-3  │           │
  │  │ db-rep-1   │  │ redis-1    │  │ nginx-1    │           │
  │  └────────────┘  └────────────┘  └────────────┘           │
  └─────────────────────────────────────────────────────────────┘

  Overlay Network (VXLAN tunnels between all nodes)
  Routing Mesh (any node port reaches any service replica)
```

---

## Swarm Services & Scaling

```bash
# ── Create service ────────────────────────────────────────────────────────────
docker service create \
  --name web \
  --replicas 3 \
  --publish 80:80 \
  --network webnet \
  --constraint 'node.role==worker' \
  nginx:alpine

# ── List services ─────────────────────────────────────────────────────────────
docker service ls
docker service ps web          # Tasks (containers) for service
docker service inspect web     # Full service config

# ── Scale ─────────────────────────────────────────────────────────────────────
docker service scale web=5           # Scale to 5 replicas
docker service scale web=5 api=3     # Scale multiple

# ── Update service config ─────────────────────────────────────────────────────
docker service update \
  --image nginx:1.25 \             # New image version
  --update-parallelism 2 \         # Update 2 at a time
  --update-delay 30s \             # Wait 30s between batches
  web

# ── Logs ──────────────────────────────────────────────────────────────────────
docker service logs web            # All replicas' logs
docker service logs -f web         # Follow logs

# ── Remove service ────────────────────────────────────────────────────────────
docker service rm web
```

---

## Rolling Updates & Rollbacks

```bash
# ── Update with zero downtime ──────────────────────────────────────────────────
docker service update \
  --image myapp:v2.0 \
  --update-parallelism 1 \          # Update 1 replica at a time
  --update-delay 30s \              # Wait 30s before next
  --update-monitor 60s \            # Monitor for 60s after update
  --update-failure-action rollback \ # Auto-rollback on failure!
  --update-order start-first \      # Start new before stopping old
  myapp

# Visual of rolling update:
# Time 0:  [v1] [v1] [v1]
# Time 1:  [v2] [v1] [v1]  ← replica 1 updated
# Time 2:  [v2] [v2] [v1]  ← replica 2 updated
# Time 3:  [v2] [v2] [v2]  ← replica 3 updated

# ── Manual rollback ────────────────────────────────────────────────────────────
docker service rollback myapp

# ── Watch update progress ──────────────────────────────────────────────────────
watch docker service ps myapp
```

---

## Kubernetes Migration Path

```yaml
# Compose to Kubernetes (using Kompose)
# Install: https://kompose.io/

# Convert docker-compose.yml to K8s manifests:
kompose convert -f docker-compose.yml -o k8s/

# Generated files:
# k8s/web-deployment.yaml
# k8s/web-service.yaml
# k8s/db-deployment.yaml
# k8s/db-service.yaml
# k8s/web-persistentvolumeclaim.yaml
```

```yaml
# Example Kubernetes Deployment (equivalent to Compose service)
# k8s/app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Start 1 new before stopping old
      maxUnavailable: 0  # Zero downtime
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: app
          image: myrepo/myapp:v2.1.3
          ports:
            - containerPort: 3000
          env:
            - name: NODE_ENV
              value: production
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: password
          resources:
            limits:
              cpu: "500m"
              memory: "256Mi"
            requests:
              cpu: "100m"
              memory: "128Mi"
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 5
          securityContext:
            runAsNonRoot: true
            runAsUser: 1001
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
            capabilities:
              drop: ["ALL"]
```

---

## Swarm Commands Quick Reference

```bash
# CLUSTER MANAGEMENT
docker swarm init                  # Initialize swarm
docker swarm join --token ... HOST # Join as worker
docker swarm leave --force         # Leave swarm
docker node ls                     # List nodes
docker node update --availability drain NODE  # Drain (maintenance)
docker node rm NODE                # Remove node

# SERVICE MANAGEMENT
docker service create OPTIONS IMAGE  # Create service
docker service ls                    # List services
docker service ps SERVICE            # List tasks
docker service scale SERVICE=N       # Scale
docker service update OPTIONS SERVICE # Update
docker service rollback SERVICE      # Rollback
docker service rm SERVICE            # Remove

# STACK MANAGEMENT
docker stack deploy -c file.yml STACK  # Deploy stack
docker stack ls                        # List stacks
docker stack services STACK            # Stack services
docker stack ps STACK                  # Stack tasks
docker stack rm STACK                  # Remove stack

# SECRETS
docker secret create NAME FILE         # Create secret
docker secret ls                       # List secrets
docker secret rm NAME                  # Remove secret

# CONFIGS
docker config create NAME FILE         # Create config
docker config ls                       # List configs
docker config rm NAME                  # Remove config
```

---

**Next:** [CI/CD Guide →](../09_cicd/cicd_guide.md)
