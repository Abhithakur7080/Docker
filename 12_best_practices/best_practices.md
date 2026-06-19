# 🏆 Module 12 — Docker Best Practices

> **Level:** 🏆 Expert | **Reference:** Master guide for production Docker

---

## 📖 Table of Contents

- [Image Best Practices](#image-best-practices)
- [Dockerfile Patterns](#dockerfile-patterns)
- [Compose Best Practices](#compose-best-practices)
- [Performance Optimization](#performance-optimization)
- [Operational Excellence](#operational-excellence)
- [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
- [Decision Framework](#decision-framework)

---

## Image Best Practices

### Base Image Selection

```
DECISION TREE: Choosing a Base Image
──────────────────────────────────────────────────────────────────

Do you need a full Linux system?
├── No (static binary) → FROM scratch            (0MB)
├── No (compiled language) → FROM distroless     (5-20MB)
└── Yes
    ├── musl libc OK? → FROM alpine:3.x          (7MB)
    │   ⚠️ Some packages work differently on musl
    ├── Need glibc? → FROM debian:12-slim        (75MB)
    │   or language-specific:
    │   - node:20-slim
    │   - python:3.12-slim
    │   - eclipse-temurin:21-jre-jammy
    └── Need full tooling? → FROM ubuntu:22.04   (77MB)
        (only for development images!)

RECOMMENDATION:
  Production apps:  Alpine or language:slim
  Static binaries:  scratch or distroless
  Development:      Full image for tooling
```

### Version Pinning Strategy

```dockerfile
# ❌ Floating — unpredictable builds
FROM node:latest
FROM python:3
FROM ubuntu

# ❌ Minor floating — still changes
FROM node:20
FROM python:3.12

# ✅ Patch-pinned — stable, predictable
FROM node:20.11.1-alpine3.19
FROM python:3.12.2-slim-bookworm

# ✅ Digest-pinned — immutable (supply chain security)
FROM node:20.11.1-alpine3.19@sha256:abc123def456...

# How to get a digest:
# docker pull node:20.11.1-alpine3.19
# docker inspect node:20.11.1-alpine3.19 | grep -i digest
```

---

## Dockerfile Patterns

### The Optimal Layer Order

```dockerfile
# 1. Most stable → least stable (maximize cache hits)
FROM node:20-alpine

# 2. System deps (rarely change)
RUN apk add --no-cache dumb-init

# 3. Application metadata
WORKDIR /app
ENV NODE_ENV=production

# 4. Dependency manifest (changes occasionally)
COPY package*.json ./

# 5. Install deps (expensive, cache this!)
RUN npm ci --only=production && npm cache clean --force

# 6. Application code (changes often)
COPY . .

# 7. Build (only if code changed)
RUN npm run build

# 8. Runtime config (rarely changes)
USER node
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

### Signal Handling (Critical for Graceful Shutdown)

```dockerfile
# ❌ Problem: Shell form wraps CMD in /bin/sh, signals not forwarded!
CMD node server.js          # PID 1 = /bin/sh, not node!

# ✅ Solution 1: Exec form
CMD ["node", "server.js"]   # PID 1 = node ✅

# ✅ Solution 2: dumb-init (handles zombies + signals)
RUN apk add --no-cache dumb-init
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]   # dumb-init → node, signals forwarded ✅

# ✅ Solution 3: tini
RUN apk add --no-cache tini
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "server.js"]
```

```javascript
// Application side: handle SIGTERM gracefully
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down gracefully...');
  await server.close();    // Stop accepting new requests
  await db.disconnect();   // Close DB connections
  process.exit(0);         // Clean exit
});
```

### Health Check Best Practices

```dockerfile
# ❌ Bad: curl might not be installed, no timeout
HEALTHCHECK CMD curl http://localhost:3000

# ✅ Good: explicit timeout + status check
HEALTHCHECK --interval=30s \
            --timeout=5s \
            --start-period=30s \
            --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1

# ✅ Better: Dedicated health binary (no shell deps)
# Add a healthcheck binary to your app
HEALTHCHECK --interval=30s CMD ["/app/healthcheck"]

# Health endpoint should check:
# - Application is responsive
# - Database connection is alive
# - Cache connection is alive
# - Return 200 with JSON: {"status":"ok","db":"ok","cache":"ok"}
```

---

## Compose Best Practices

### Service Naming & Organization

```yaml
# ✅ Descriptive, consistent names
services:
  web-proxy:           # Role-based naming
  api-server:
  db-primary:
  cache-server:
  queue-worker:

# ✅ Use YAML anchors for DRY config
x-app-base: &app-base
  image: ${IMAGE}:${TAG}
  restart: unless-stopped
  networks: [backend]
  logging:
    driver: json-file
    options:
      max-size: "10m"

services:
  api:
    <<: *app-base          # Inherit from anchor
    environment:
      ROLE: api

  worker:
    <<: *app-base          # Same base
    environment:
      ROLE: worker
    command: ["node", "worker.js"]
```

### Environment Management

```bash
# File hierarchy (highest priority first):
# 1. Shell environment variables
# 2. .env file in compose directory
# 3. Default values in compose file

# Development setup:
.env.example    ← Template (committed to git)
.env            ← Local overrides (gitignored!)
.env.test       ← Test environment
.env.staging    ← Staging (gitignored!)

# Usage:
docker compose --env-file .env.staging up
```

```yaml
# compose.yml (good pattern)
services:
  app:
    environment:
      # Validate required vars — fail fast if missing!
      DB_PASSWORD: ${DB_PASSWORD:?DB_PASSWORD is required}
      API_KEY: ${API_KEY:?API_KEY is required}
      # Optional with defaults:
      LOG_LEVEL: ${LOG_LEVEL:-info}
      PORT: ${PORT:-3000}
```

---

## Performance Optimization

### Build Performance

```
DOCKER BUILD TIME OPTIMIZATION
────────────────────────────────────────────────────────────────────

Technique                          Speedup
─────────────────────────────────  ────────
Layer caching (proper order)       2-10x
.dockerignore                      1.5-3x
Multi-stage builds                 (smaller, faster push/pull)
BuildKit parallel stages           1.5-2x
BuildKit cache mounts              3-5x (for package managers)
Remote build cache (CI)            2-8x
```

```dockerfile
# BuildKit cache mounts — huge speedup for packages!

# npm:
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# pip:
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# apt:
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y curl

# Maven:
RUN --mount=type=cache,target=/root/.m2 \
    mvn package -DskipTests

# Go modules:
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download
```

### Runtime Performance

```yaml
services:
  db:
    # PostgreSQL performance tuning
    environment:
      POSTGRES_SHARED_BUFFERS: 256MB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 768MB
      POSTGRES_MAINTENANCE_WORK_MEM: 64MB
      POSTGRES_CHECKPOINT_COMPLETION_TARGET: "0.9"
      POSTGRES_WAL_BUFFERS: 16MB
      POSTGRES_DEFAULT_STATISTICS_TARGET: "100"
    shm_size: '256mb'     # Critical for PostgreSQL!
    command: >
      postgres
      -c shared_buffers=256MB
      -c max_connections=200

  redis:
    # Redis performance config
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --hz 100
      --appendonly yes
      --appendfsync everysec     # Balance between perf & durability
```

---

## Operational Excellence

### Structured Logging

```javascript
// Application: Use structured JSON logs
const logger = {
  info: (msg, meta = {}) => console.log(JSON.stringify({
    timestamp: new Date().toISOString(),
    level: 'info',
    message: msg,
    service: process.env.SERVICE_NAME,
    ...meta
  }))
};

// Good log entry:
logger.info('Request processed', {
  requestId: req.id,
  method: req.method,
  path: req.path,
  statusCode: res.statusCode,
  durationMs: Date.now() - req.startTime
});
```

```yaml
# Compose: Configure logging
services:
  app:
    logging:
      driver: json-file
      options:
        max-size: "10m"     # Prevent disk filling
        max-file: "5"       # Keep 5 rotated files
        tag: "{{.Name}}/{{.ID}}"

    # OR: Send to centralized logging
    logging:
      driver: fluentd
      options:
        fluentd-address: "localhost:24224"
        tag: "docker.{{.Name}}"
```

### Container Labels

```yaml
# Use labels for operations, monitoring, management
services:
  api:
    labels:
      # Standard OCI labels
      org.opencontainers.image.source: "https://github.com/org/repo"
      org.opencontainers.image.version: "2.1.3"
      org.opencontainers.image.created: "2024-01-15T10:00:00Z"

      # Custom operational labels
      com.myapp.team: "platform"
      com.myapp.env: "production"
      com.myapp.service: "api"
      com.myapp.tier: "backend"

      # Traefik routing labels (if using Traefik)
      traefik.enable: "true"
      traefik.http.routers.api.rule: "Host(`api.myapp.com`)"

      # Prometheus scraping labels
      prometheus.io/scrape: "true"
      prometheus.io/port: "3000"
      prometheus.io/path: "/metrics"
```

### Dependency Health Waiting

```bash
# ── In entrypoint script ─────────────────────────────────────────────────────
#!/bin/sh
# wait-for.sh — wait for a service to be ready

HOST="$1"
PORT="$2"
shift 2

until nc -z "$HOST" "$PORT"; do
  echo "Waiting for $HOST:$PORT..."
  sleep 2
done

exec "$@"
```

```dockerfile
COPY wait-for.sh /usr/local/bin/wait-for
RUN chmod +x /usr/local/bin/wait-for

CMD ["wait-for", "db:5432", "--", "node", "server.js"]
```

---

## Anti-Patterns to Avoid

```
❌ ANTI-PATTERN                    ✅ CORRECT APPROACH
─────────────────────────────────  ─────────────────────────────────────

Running as root                    USER instruction with non-root user

FROM ubuntu (floating tag)         FROM ubuntu:22.04 (pinned version)

RUN apt-get update (separate)      RUN apt-get update && apt-get install
RUN apt-get install -y curl        (in one RUN, with cleanup)
                                   && rm -rf /var/lib/apt/lists/*

Storing secrets in ENV             Docker secrets, vault, runtime injection

COPY . . (before npm install)      COPY package.json first
                                   RUN npm install
                                   COPY . .        (cache-friendly order)

CMD node server.js (shell form)    CMD ["node", "server.js"] (exec form)

Mounting /var/run/docker.sock      Don't. Use proper build systems.
in production

No HEALTHCHECK defined             Define HEALTHCHECK for all services

No resource limits                 Set memory and CPU limits

--privileged in production         Drop ALL caps, add only required

No .dockerignore file              Always have .dockerignore

apt-get install without            apt-get install -y --no-install-recommends
--no-install-recommends            (saves space)

Single stage for everything        Multi-stage: separate build from runtime

No restart policy                  restart: unless-stopped (or on-failure)

Plain text passwords in compose    Use secrets or env_file (.gitignored)

Latest tag in production           Specific version tags (v2.1.3)

No log rotation                    max-size and max-file logging options
```

---

## Decision Framework

### Should I use Docker Compose or Kubernetes?

```
┌────────────────────────────────────────────────────────────────┐
│              ORCHESTRATION DECISION TREE                       │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Single host?                                                  │
│  ├── YES → Docker Compose (95% of cases!)                     │
│  │         Simple, fast, no overhead                          │
│  └── NO → Multiple hosts needed?                              │
│            ├── Simple → Docker Swarm                          │
│            │   Easy to set up, built-in to Docker             │
│            └── Complex / Scale → Kubernetes                   │
│                Advanced routing, auto-scaling,                 │
│                self-healing, large teams                       │
│                                                                │
│  When to choose Kubernetes:                                    │
│  ✅ > 5 microservices                                          │
│  ✅ Need advanced auto-scaling                                 │
│  ✅ Multiple teams / large org                                 │
│  ✅ Need fine-grained RBAC                                     │
│  ✅ Service mesh requirements                                  │
│  ✅ Multi-cloud/hybrid deployments                             │
└────────────────────────────────────────────────────────────────┘
```

### Image Strategy Decision

```
Need to run:           → Use image from:
─────────────────────    ─────────────────────────────────────────
Popular open source    → Official Docker Hub image (nginx, postgres)
Company service        → Private registry (ECR, GCR, GHCR)
Custom app             → Build with multi-stage Dockerfile
Lambda/serverless      → Consider serverless-specific container base
AI/ML workloads        → NVIDIA CUDA images or PyTorch images
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                   DOCKER QUICK REFERENCE                        │
├──────────────────────┬──────────────────────────────────────────┤
│ Run container        │ docker run -d -p 80:80 --name web nginx  │
│ List running         │ docker ps                                 │
│ Shell into container │ docker exec -it <name> sh                │
│ View logs            │ docker logs -f <name>                     │
│ Stop container       │ docker stop <name>                        │
│ Remove container     │ docker rm <name>                          │
│ Build image          │ docker build -t myapp:v1 .               │
│ Push image           │ docker push myrepo/myapp:v1              │
│ Full cleanup         │ docker system prune -a --volumes         │
│ Compose start        │ docker compose up -d                     │
│ Compose logs         │ docker compose logs -f                   │
│ Compose stop         │ docker compose down                      │
│ Compose rebuild      │ docker compose up -d --build             │
└──────────────────────┴──────────────────────────────────────────┘
```

---

> 🎓 **You've reached the end of the Docker learning path!**
> Check out [Kubernetes](https://kubernetes.io/docs/home/) for the next level,
> or [Docker Swarm](https://docs.docker.com/engine/swarm/) for simpler orchestration.
