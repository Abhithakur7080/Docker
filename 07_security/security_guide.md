# 🔐 Module 07 — Container Security

> **Level:** 🔴 Advanced | **Time:** ~4 hours | **Prerequisites:** Modules 01-06

---

## 📖 Table of Contents

- [Security Threat Model](#security-threat-model)
- [Image Security](#image-security)
- [Runtime Security](#runtime-security)
- [Network Security](#network-security)
- [Secrets Management](#secrets-management)
- [Scanning & Auditing](#scanning--auditing)
- [Security Checklist](#security-checklist)

---

## Security Threat Model

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DOCKER ATTACK SURFACE                            │
├──────────────────┬──────────────────────────────────────────────────┤
│  THREAT VECTOR   │  RISK & MITIGATION                               │
├──────────────────┼──────────────────────────────────────────────────┤
│ Vulnerable image │ CVEs in base OS or dependencies                  │
│                  │ → Scan images, pin versions, minimal base        │
├──────────────────┼──────────────────────────────────────────────────┤
│ Root container   │ Container escape → full host access              │
│                  │ → Always run as non-root (USER instruction)      │
├──────────────────┼──────────────────────────────────────────────────┤
│ Privileged mode  │ --privileged gives root on HOST                  │
│                  │ → Never use in production                        │
├──────────────────┼──────────────────────────────────────────────────┤
│ Exposed secrets  │ Env vars, image layers, logs                     │
│                  │ → Use Docker secrets, vault, runtime injection    │
├──────────────────┼──────────────────────────────────────────────────┤
│ Docker socket    │ Mounting /var/run/docker.sock = root on host!    │
│                  │ → Never mount in production                      │
├──────────────────┼──────────────────────────────────────────────────┤
│ Network exposure │ Unnecessary open ports                           │
│                  │ → Expose only required ports, use internal nets  │
├──────────────────┼──────────────────────────────────────────────────┤
│ Writable FS      │ Malware can write to container filesystem        │
│                  │ → Use read-only root filesystem                  │
├──────────────────┼──────────────────────────────────────────────────┤
│ Excessive caps   │ Linux capabilities can escape isolation          │
│                  │ → Drop ALL, add only what's needed               │
└──────────────────┴──────────────────────────────────────────────────┘
```

---

## Image Security

### Use Minimal Base Images

```dockerfile
# DANGER: Fat image with many attack surfaces
FROM ubuntu:22.04      # 77MB, hundreds of packages

# BETTER: Slim image
FROM debian:12-slim    # 74MB, fewer packages

# BETTER: Alpine Linux (musl-based, very minimal)
FROM alpine:3.19       # 7MB, minimal attack surface

# BEST: Distroless (no shell, no package manager!)
FROM gcr.io/distroless/nodejs20-debian12
# No apt, no bash, no wget — attacker can't do much!

# ULTIMATE: scratch (for static binaries)
FROM scratch
# Literally empty. Only your binary exists.
```

### Pin ALL Versions (Supply Chain Security)

```dockerfile
# ❌ DANGEROUS: floating tags
FROM node:latest
FROM node:20
FROM python:3-slim

# ✅ SECURE: pin to digest (immutable!)
FROM node:20.11.1-alpine3.19
# OR pin to SHA256 digest:
FROM node:20.11.1-alpine3.19@sha256:abc123...

# Pin APT packages:
RUN apt-get install -y curl=7.88.1-10+deb12u5
```

### Minimize What's in the Image

```dockerfile
# ❌ WRONG: leave build tools in final image
FROM ubuntu
RUN apt-get install -y build-essential gcc python3

# ✅ RIGHT: multi-stage, final image has only runtime
FROM golang:1.22 AS builder
RUN go build -o /app .

FROM scratch AS final           # ZERO extra tools!
COPY --from=builder /app /app
ENTRYPOINT ["/app"]
```

---

## Runtime Security

### Non-Root User

```dockerfile
# ── Method 1: Create dedicated user ─────────────────────────────────────────
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup \
            --no-create-home \
            --shell /bin/false \
            appuser

# Set ownership before switching
COPY --chown=appuser:appgroup . /app
USER appuser

# ── Method 2: Use existing user (node images) ────────────────────────────────
USER node   # node:alpine images include 'node' user (uid=1000)

# ── Method 3: Numeric UID (works without /etc/passwd) ────────────────────────
USER 65534  # nobody
```

```bash
# Verify container isn't root:
docker exec mycontainer id
# Should show: uid=1001(appuser) gid=1001(appgroup)  NOT uid=0(root)

# Run as specific user at runtime (override Dockerfile):
docker run --user 1001:1001 myimage
```

### Read-Only Root Filesystem

```bash
docker run --read-only \
  --tmpfs /tmp \             # Allow writes to /tmp
  --tmpfs /run \             # Allow writes to /run
  myapp
```

```yaml
services:
  api:
    read_only: true
    tmpfs:
      - /tmp
      - /run
      - /app/tmp
```

### Drop Linux Capabilities

```bash
# By default, containers get these capabilities:
# CHOWN, DAC_OVERRIDE, FSETID, FOWNER, MKNOD, NET_RAW,
# SETGID, SETUID, SETFCAP, SETPCAP, NET_BIND_SERVICE,
# SYS_CHROOT, KILL, AUDIT_WRITE

# ✅ Best practice: Drop all, add only what you need
docker run \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \   # If binding port <1024
  myapp
```

```yaml
services:
  nginx:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE    # Nginx binds port 80
      - CHOWN               # Change file ownership
```

### Security Options

```yaml
services:
  app:
    security_opt:
      - no-new-privileges:true   # Can't escalate privileges
      - seccomp:./seccomp.json   # Custom syscall filter
      - apparmor:myprofile       # AppArmor profile
    
    # Limit PID namespace
    pid: host                    # DANGER: shares host PIDs (rarely needed)
    # Or isolate:
    # (default is isolated)
```

### Resource Limits (Prevent DoS)

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '0.5'       # Max 50% of one CPU
          memory: 256M      # Max 256MB RAM
          pids: 100         # Max 100 processes
        reservations:
          cpus: '0.1'
          memory: 64M

    # Additional limits:
    ulimits:
      nofile:               # Max open files
        soft: 1024
        hard: 2048
      nproc:
        soft: 512
        hard: 1024
```

---

## Network Security

```yaml
services:
  db:
    networks:
      - data                # Internal only
    # No 'ports:' — not exposed to host!

  api:
    networks:
      - frontend
      - data

  nginx:
    ports:
      - "80:80"             # Only this faces internet
    networks:
      - frontend

networks:
  frontend:
    driver: bridge
  data:
    driver: bridge
    internal: true          # ← No internet access for DB!
```

```
Security Zones:

  Internet
     │
     ▼
┌─────────┐
│  nginx  │ ← Only public-facing component
└────┬────┘
     │ frontend network
┌────▼────┐
│   api   │ ← Not directly exposed
└────┬────┘
     │ data network (internal: true)
┌────▼────┐
│   db    │ ← Zero internet access
└─────────┘
```

---

## Secrets Management

### ❌ Anti-Patterns (NEVER DO THESE)

```dockerfile
# DANGER: Secret in Dockerfile (visible in image history!)
ENV DB_PASSWORD=mysecret123

# DANGER: Secret as ARG (visible in docker history!)
ARG DB_PASSWORD
RUN curl -H "Auth: $DB_PASSWORD" https://api.example.com
```

```yaml
# DANGER: Plain text secret in compose file (committed to git!)
services:
  app:
    environment:
      DB_PASSWORD: "mysecret123"
```

### ✅ Correct Approaches

#### 1. Docker Secrets (Swarm / Compose v2.3+)

```yaml
services:
  app:
    image: myapp
    secrets:
      - db_password
      - api_key
    environment:
      # App reads from file, not env var
      DB_PASSWORD_FILE: /run/secrets/db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt    # Local file (gitignored!)

  # OR from external (Docker Swarm):
  api_key:
    external: true
    name: production_api_key
```

#### 2. Environment File (`.env`)

```bash
# .env (gitignored!)
DB_PASSWORD=mysecret123
REDIS_PASSWORD=anothersecret

# .gitignore
.env
.env.*
secrets/
```

```yaml
services:
  app:
    env_file:
      - .env          # Loaded from file, not hardcoded
```

#### 3. BuildKit Secret Mounts (for build secrets)

```dockerfile
# Secret used at build time, NOT stored in layer!
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm install @private/package
```

```bash
docker build --secret id=npmrc,src=$HOME/.npmrc .
```

#### 4. External Secrets Managers

```
HashiCorp Vault → vault agent sidecar injects secrets at runtime
AWS Secrets Manager → AWS SDK fetches secrets
Azure Key Vault → Azure managed identity
Google Secret Manager → Workload Identity

Pattern:
  App starts → Fetch secret from vault at runtime → Use in memory
  (Secrets never touch disk or image layers!)
```

---

## Scanning & Auditing

### Image Vulnerability Scanning

```bash
# ── Docker Scout (built-in) ──────────────────────────────────────────────────
docker scout cves myimage:latest
docker scout quickview myimage:latest
docker scout recommendations myimage:latest

# ── Trivy (comprehensive) ────────────────────────────────────────────────────
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image myimage:latest

# Fail build if HIGH/CRITICAL CVEs found (for CI):
docker run --rm aquasec/trivy image \
  --exit-code 1 \
  --severity HIGH,CRITICAL \
  myimage:latest

# ── Snyk ────────────────────────────────────────────────────────────────────
snyk container test myimage:latest

# ── Grype ────────────────────────────────────────────────────────────────────
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  anchore/grype:latest myimage:latest
```

### Runtime Security Monitoring

```bash
# ── Falco (real-time threat detection) ──────────────────────────────────────
docker run -d --name falco \
  --privileged \
  -v /var/run/docker.sock:/host/var/run/docker.sock \
  -v /dev:/host/dev \
  -v /proc:/host/proc:ro \
  falcosecurity/falco:latest

# Falco rules detect:
# - Shell spawned in container
# - File write in /etc or /usr
# - Network outbound from DB containers
# - Privilege escalation attempts
```

### Docker Bench Security

```bash
# Run CIS Docker Benchmark
docker run -it --net host --pid host --userns host --cap-add audit_control \
  -e DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST \
  -v /etc:/etc:ro \
  -v /usr/bin/containerd:/usr/bin/containerd:ro \
  -v /usr/bin/runc:/usr/bin/runc:ro \
  -v /usr/lib/systemd:/usr/lib/systemd:ro \
  -v /var/lib:/var/lib:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  --label docker_bench_security \
  docker/docker-bench-security
```

---

## Security Checklist

```
IMAGE SECURITY
──────────────
[ ] Use minimal base image (Alpine, distroless, or scratch)
[ ] Pin ALL versions (base image + packages) with digests
[ ] Multi-stage build — no build tools in final image
[ ] Scan image for CVEs (Trivy/Snyk/Scout) in CI pipeline
[ ] Sign images with Docker Content Trust or Cosign
[ ] No secrets/credentials in Dockerfile or image layers
[ ] .dockerignore excludes sensitive files
[ ] No SUID/SGID files: RUN find / -perm /6000 -exec chmod a-s {} \;

RUNTIME SECURITY
────────────────
[ ] Run as non-root user (USER 1001)
[ ] Read-only root filesystem (--read-only)
[ ] Drop ALL capabilities, add only required (--cap-drop ALL)
[ ] no-new-privileges security option
[ ] Memory and CPU limits set
[ ] PID limits set
[ ] No --privileged flag
[ ] No /var/run/docker.sock mount
[ ] Seccomp profile applied

NETWORK SECURITY
────────────────
[ ] Minimal exposed ports
[ ] Internal networks for DB/cache tier
[ ] TLS/mTLS for service-to-service communication
[ ] Network policies (if using Kubernetes)
[ ] No host network mode in production

SECRETS MANAGEMENT
──────────────────
[ ] No secrets in environment variables (plain text)
[ ] Use Docker secrets, vault, or secret manager
[ ] .env files gitignored
[ ] Rotate secrets regularly
[ ] Audit secret access
```

---

**Next:** [Orchestration Guide →](../08_orchestration/swarm_guide.md)
