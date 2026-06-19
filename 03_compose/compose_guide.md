# 🐳 Module 03 — Docker Compose Guide

> **Level:** 🟡 Intermediate | **Time:** ~3 hours | **Prerequisites:** Modules 01-02

---

## 📖 Table of Contents

- [What is Docker Compose?](#what-is-docker-compose)
- [Compose File Structure](#compose-file-structure)
- [Services Deep Dive](#services-deep-dive)
- [Networks in Compose](#networks-in-compose)
- [Volumes in Compose](#volumes-in-compose)
- [Profiles & Scaling](#profiles--scaling)
- [Environment & Secrets](#environment--secrets)
- [Override Files](#override-files)
- [Health Checks & Dependencies](#health-checks--dependencies)

---

## What is Docker Compose?

Docker Compose is a tool for defining and running **multi-container applications** using a YAML configuration file.

```
Without Compose (manual hell):         With Compose:
──────────────────────────────         ─────────────
docker network create mynet            docker compose up
docker volume create pgdata
docker run -d --name db \
  --network mynet \
  -v pgdata:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=secret \
  postgres:16

docker run -d --name redis \
  --network mynet \
  redis:7-alpine

docker run -d --name app \
  --network mynet \
  -p 3000:3000 \
  -e DB_HOST=db \
  myapp:latest

# ... and you have to remember all of this!
```

---

## Compose File Structure

```yaml
# docker-compose.yml
# ─────────────────────────────────────────────────────────────
#                     TOP-LEVEL KEYS
# ─────────────────────────────────────────────────────────────

name: myproject          # Project name (override COMPOSE_PROJECT_NAME)

services:                # Container definitions
  web: ...
  db: ...

networks:                # Custom network definitions
  frontend: ...
  backend: ...

volumes:                 # Named volume definitions
  pgdata: ...

configs:                 # Config files (Swarm + Compose v2.3+)
  nginx_conf: ...

secrets:                 # Secrets management
  db_password: ...

# ─────────────────────────────────────────────────────────────
#                   VERSION NOTE
# ─────────────────────────────────────────────────────────────
# ⚠️  Modern Compose (v2+) does NOT require "version:" key
# ✅  Just omit it — Docker Compose auto-detects the schema
```

---

## Services Deep Dive

```yaml
services:
  webapp:
    # ── Image Source ─────────────────────────────────────────
    image: nginx:alpine           # Use pre-built image
    # OR
    build:
      context: ./app             # Build from local Dockerfile
      dockerfile: Dockerfile.prod
      args:
        NODE_ENV: production
      cache_from:
        - myapp:cache
      target: production         # Multi-stage build target

    # ── Container Identity ───────────────────────────────────
    container_name: my-webapp    # Override generated name
    hostname: webapp

    # ── Port Mapping ─────────────────────────────────────────
    ports:
      - "80:80"                  # host:container
      - "443:443"
      - "127.0.0.1:8080:8080"   # Bind to specific host IP
      - target: 3000             # Verbose syntax
        published: 3000
        protocol: tcp

    # ── Environment ──────────────────────────────────────────
    environment:
      NODE_ENV: production
      PORT: 3000
      DB_HOST: db                # Use service name as hostname!
    env_file:
      - .env
      - .env.local               # Override with local settings

    # ── Volumes ──────────────────────────────────────────────
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro   # Bind mount (read-only)
      - static_files:/var/www/html              # Named volume
      - type: volume                            # Verbose syntax
        source: app_data
        target: /app/data

    # ── Networking ───────────────────────────────────────────
    networks:
      - frontend
      - backend
    network_mode: host           # Use host network (alternative)

    # ── Dependencies ─────────────────────────────────────────
    depends_on:
      db:
        condition: service_healthy    # Wait for health check!
      redis:
        condition: service_started    # Just wait for start

    # ── Restart Policy ───────────────────────────────────────
    restart: unless-stopped
    # no | always | on-failure | unless-stopped

    # ── Resource Limits ──────────────────────────────────────
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M
      replicas: 2                # Scale replicas

    # ── Health Check ─────────────────────────────────────────
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    # ── Logging ──────────────────────────────────────────────
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

    # ── User & Security ──────────────────────────────────────
    user: "1001:1001"
    read_only: true              # Read-only root filesystem
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

    # ── Labels ───────────────────────────────────────────────
    labels:
      app.version: "2.1.0"
      traefik.enable: "true"

    # ── Profiles ─────────────────────────────────────────────
    profiles:
      - debug                    # Only start with --profile debug
```

---

## Networks in Compose

```yaml
# Default behavior:
# Compose creates ONE default network: projectname_default
# ALL services join it automatically
# Services communicate using service NAME as hostname!

services:
  web:
    networks: [frontend, backend]
    image: nginx

  api:
    networks: [backend]
    image: myapi

  db:
    networks: [backend]         # NOT accessible from frontend!
    image: postgres

networks:
  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

  backend:
    driver: bridge
    internal: true              # No external access!

  # Reuse an existing external network:
  monitoring:
    external: true
    name: monitoring_network
```

```
Network Topology Visualization:

  Internet
     │
     ▼
┌────────────┐
│  frontend  │ (bridge, external)
│  network   │
│            │
│   ┌──────┐ │
│   │ web  │ │
│   └──┬───┘ │
└──────┼─────┘
       │
┌──────▼──────────────────┐
│      backend network     │ (bridge, internal)
│                          │
│   ┌───┐   ┌────┐  ┌────┐│
│   │web│   │ api│  │ db ││
│   └───┘   └────┘  └────┘│
└──────────────────────────┘
```

---

## Volumes in Compose

```yaml
volumes:
  # Named volume (managed by Docker)
  pgdata:
    driver: local

  # External volume (pre-existing, not created by Compose)
  legacy_data:
    external: true
    name: old_project_data

  # NFS volume
  nfs_share:
    driver: local
    driver_opts:
      type: nfs
      o: addr=nfs-server.local,rw
      device: ":/exports/data"

  # Custom tmpfs
  cache:
    driver: local
    driver_opts:
      type: tmpfs
      device: tmpfs
      o: size=100m

services:
  db:
    volumes:
      - pgdata:/var/lib/postgresql/data      # Named volume
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro  # Bind mount
      - type: tmpfs                          # In-memory
        target: /tmp
```

---

## Environment & Secrets

```yaml
# ── .env file (auto-loaded from compose file directory) ──────────────────────
# POSTGRES_PASSWORD=secret123
# NODE_ENV=production

services:
  db:
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}   # From .env

  app:
    secrets:
      - db_password
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt   # From file

  # Docker Swarm secret (external):
  api_key:
    external: true
    name: myapp_api_key
```

---

## Override Files

```
Compose loads multiple files and MERGES them:

docker compose up                              # loads docker-compose.yml
docker compose -f a.yml -f b.yml up            # explicit files
docker compose --env-file .env.prod up         # custom env file

Standard override pattern:
  docker-compose.yml        ← Base config (committed to git)
  docker-compose.override.yml  ← Dev overrides (auto-loaded, gitignored)
  docker-compose.prod.yml   ← Production overrides

Merge behavior:
  ─────────────────────────────────────────────────
  Key          │ Behavior
  ─────────────────────────────────────────────────
  image        │ Override (last wins)
  build        │ Override (last wins)
  ports        │ MERGE (unique entries added)
  volumes      │ MERGE (unique entries added)
  environment  │ MERGE (last wins per key)
  networks     │ MERGE (unique entries added)
  command      │ Override (last wins)
  ─────────────────────────────────────────────────
```

---

## Health Checks & Dependencies

```yaml
# ── Dependency Flow ──────────────────────────────────────────────────────────
#
#   app ──depends_on──▶ db (healthy) ──▶ redis (started)
#                               │
#                      wait for HEALTHCHECK to pass

services:
  app:
    depends_on:
      db:
        condition: service_healthy   # ✅ Waits for DB to be ready!
      redis:
        condition: service_started   # Just started (not necessarily ready)
      migrations:
        condition: service_completed_successfully  # One-shot task done

  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  migrations:
    image: myapp:latest
    command: ["npm", "run", "migrate"]
    depends_on:
      db:
        condition: service_healthy
    restart: "no"   # Run once and exit
```

---

## Profiles & Scaling

```yaml
# ── Profiles: conditionally enable services ──────────────────────────────────
services:
  app:
    image: myapp
    # No profile = always started

  db:
    image: postgres
    # No profile = always started

  adminer:              # DB admin UI — only in dev
    image: adminer
    profiles: [dev, tools]

  mailhog:              # Fake SMTP — only in dev
    image: mailhog/mailhog
    profiles: [dev]

  monitoring:           # Only when explicitly enabled
    image: grafana/grafana
    profiles: [monitoring]

# Usage:
# docker compose up                    ← app + db only
# docker compose --profile dev up      ← + adminer + mailhog
# docker compose --profile monitoring up  ← + monitoring

# ── Scaling ──────────────────────────────────────────────────────────────────
# docker compose up --scale app=3
# deploy.replicas for Swarm mode
services:
  app:
    image: myapp
    deploy:
      replicas: 3        # Swarm mode
      update_config:
        parallelism: 1   # Update 1 replica at a time
        delay: 10s
      restart_policy:
        condition: on-failure
        max_attempts: 3
```

---

**Next:** [Networking Guide →](../04_networking/networking_guide.md)
