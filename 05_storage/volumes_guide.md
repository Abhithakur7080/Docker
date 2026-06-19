# 🐳 Module 05 — Volumes & Storage

> **Level:** 🟡 Intermediate | **Time:** ~2 hours | **Prerequisites:** Module 03

---

## 📖 Table of Contents

- [Storage Types Overview](#storage-types-overview)
- [Named Volumes](#named-volumes)
- [Bind Mounts](#bind-mounts)
- [tmpfs Mounts](#tmpfs-mounts)
- [Volume Drivers](#volume-drivers)
- [Backup & Restore](#backup--restore)
- [Common Patterns](#common-patterns)

---

## Storage Types Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER STORAGE OPTIONS                       │
├──────────────────┬──────────────────┬──────────────────────────┤
│   NAMED VOLUME   │   BIND MOUNT     │        TMPFS             │
├──────────────────┼──────────────────┼──────────────────────────┤
│ Managed by       │ Managed by you   │ In-memory only           │
│ Docker           │                  │                          │
│                  │                  │                          │
│ /var/lib/docker  │ Any host path    │ Never persisted          │
│ /volumes/...     │ you specify      │                          │
│                  │                  │                          │
│ ✅ Portable      │ ✅ Direct access  │ ✅ Fast (RAM speed)      │
│ ✅ Persistent    │ ✅ Real-time edit │ ✅ Secure (no disk)      │
│ ✅ Backup easy   │ ✅ Dev workflow   │ ❌ Lost on stop          │
│ ❌ No direct OS  │ ❌ Host path tied │ ❌ Not persisted         │
│    path access   │ ❌ Perm issues    │ ❌ Not shared            │
└──────────────────┴──────────────────┴──────────────────────────┘

USE:  Volumes for production data
      Bind mounts for development
      tmpfs for secrets/temp files
```

### Visual: Where Data Lives

```
HOST FILESYSTEM
─────────────────────────────────────────────────────────────────

  /var/lib/docker/volumes/mydata/_data   ← Named Volume
         ▲
         │
         │ managed by Docker (you don't touch this directly)
         │
┌────────┴──────────────────────────────────────────────────────┐
│                      CONTAINER                                │
│   /app/data          ← Volume mount point                     │
│   /host-files        ← Bind mount point                       │
│   /tmp/secrets       ← tmpfs mount                            │
└────────┬──────────────────────────────────────────────────────┘
         │
         │ direct mapping
         ▼
  /home/user/myproject   ← Bind Mount source (host path)
  (RAM)                  ← tmpfs (never hits disk)
```

---

## Named Volumes

```bash
# ── Create & Manage ──────────────────────────────────────────────────────────
docker volume create mydata                    # Create
docker volume create --driver local mydata     # Explicit driver
docker volume ls                               # List
docker volume inspect mydata                   # Details
docker volume rm mydata                        # Remove (must be unused)
docker volume prune                            # Remove all unused

# ── Use in Containers ────────────────────────────────────────────────────────
docker run -v mydata:/app/data nginx           # Short syntax
docker run --mount type=volume,source=mydata,target=/app/data nginx  # Long syntax

# ── Anonymous Volumes ────────────────────────────────────────────────────────
docker run -v /app/data nginx                  # Docker generates name
# Use case: Inherit VOLUME declared in image (populate with image content)
```

```yaml
# In Docker Compose:
services:
  db:
    image: postgres:16
    volumes:
      - pgdata:/var/lib/postgresql/data       # Named
      - logs:/var/log/postgresql              # Named

  api:
    volumes:
      - ./uploads:/app/uploads               # Bind mount
      - type: volume                         # Verbose named volume
        source: cache
        target: /app/.cache
        read_only: false

volumes:
  pgdata:
    driver: local
  logs:
    driver: local
  cache:
    driver: local
```

---

## Bind Mounts

```bash
# ── Basic Bind Mount ──────────────────────────────────────────────────────────
docker run -v /host/path:/container/path nginx          # Short
docker run --mount type=bind,source=/host,target=/app nginx  # Long

# ── Read-only ────────────────────────────────────────────────────────────────
docker run -v /host/config:/etc/app:ro nginx            # :ro suffix
docker run --mount type=bind,source=/host,target=/app,readonly nginx

# ── Consistency Options (macOS performance) ───────────────────────────────────
docker run -v /host:/app:cached nginx    # Host is source of truth
docker run -v /host:/app:delegated nginx # Container is source of truth
docker run -v /host:/app:consistent nginx # Full consistency (default)
```

### Development Workflow with Bind Mounts

```yaml
# docker-compose.override.yml (for development)
services:
  api:
    volumes:
      - .:/app                    # Live code sync
      - /app/node_modules         # Don't overwrite node_modules!
    command: npm run dev          # Hot reload in dev
    environment:
      NODE_ENV: development
```

```
DEVELOPMENT FLOW:
─────────────────

Your Editor          Bind Mount          Container
   │                    │                   │
   │  Edit server.js    │                   │
   ├──────────────────▶ │                   │
   │                    │ Synced instantly  │
   │                    ├──────────────────▶│
   │                    │                   │ Nodemon detects
   │                    │                   │ change → restart
   │                    │                   │
   │ See changes at     │                   │
   │ localhost:3000      ◀─────────────────── │
```

---

## tmpfs Mounts

```bash
# ── Basic tmpfs ──────────────────────────────────────────────────────────────
docker run --tmpfs /tmp nginx                          # Basic
docker run --mount type=tmpfs,destination=/tmp nginx   # Verbose

# ── Options ──────────────────────────────────────────────────────────────────
docker run --mount type=tmpfs,destination=/tmp,tmpfs-size=100m nginx
docker run --mount type=tmpfs,destination=/tmp,tmpfs-mode=1770 nginx
```

```yaml
# In Compose:
services:
  app:
    tmpfs:
      - /tmp           # Simple
      - /run           # Multiple

    # OR with options:
    volumes:
      - type: tmpfs
        target: /tmp
        tmpfs:
          size: 104857600  # 100MB in bytes
```

**Use cases:**
- Storing secrets in memory (no disk trace)
- Session data that doesn't need persistence
- Build artifacts during multi-stage builds
- Temporary computation files

---

## Volume Drivers

```
DEFAULT DRIVER (local):
  - Stores in /var/lib/docker/volumes/
  - Only accessible on single host
  - Best for most use cases

CLOUD DRIVERS:
  - docker/cloudstor (AWS EFS, Azure File Share)
  - rexray/ebs (AWS EBS)
  - NetApp Trident (NetApp storage)

NFS DRIVER (local with NFS options):
```

```yaml
volumes:
  # NFS Mount
  nfs_data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=nfs.example.com,rw,nfsvers=4
      device: ":/exports/data"

  # CIFS/SMB Mount
  smb_data:
    driver: local
    driver_opts:
      type: cifs
      o: username=user,password=pass,vers=3.0
      device: "//server/share"

  # tmpfs as named volume
  ram_cache:
    driver: local
    driver_opts:
      type: tmpfs
      device: tmpfs
      o: size=100m
```

---

## Backup & Restore

### Backup Named Volume

```bash
# ── Method 1: Tar archive ─────────────────────────────────────────────────────
docker run --rm \
  -v mydata:/source:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/mydata_backup.tar.gz -C /source .

# ── Method 2: rsync ──────────────────────────────────────────────────────────
docker run --rm \
  -v mydata:/source:ro \
  -v /backup/dir:/dest \
  alpine sh -c "apk add rsync && rsync -av /source/ /dest/"
```

### Restore Named Volume

```bash
# Create new volume and restore from backup
docker volume create mydata_restored

docker run --rm \
  -v mydata_restored:/dest \
  -v $(pwd):/backup \
  alpine tar xzf /backup/mydata_backup.tar.gz -C /dest
```

### Database Backup Patterns

```bash
# ── PostgreSQL ────────────────────────────────────────────────────────────────
docker exec postgres_db pg_dumpall -U admin > backup.sql
docker exec postgres_db pg_dump -U admin mydb | gzip > db_backup.sql.gz

# ── MySQL ─────────────────────────────────────────────────────────────────────
docker exec mysql_db mysqldump -u root -p mydb > backup.sql

# ── MongoDB ───────────────────────────────────────────────────────────────────
docker exec mongo_db mongodump --out /backup
docker cp mongo_db:/backup ./mongo_backup
```

### Automated Backup (Compose)

```yaml
services:
  db-backup:
    image: postgres:16
    command: >
      sh -c "while true; do
        pg_dump -h db -U $$POSTGRES_USER $$POSTGRES_DB > /backups/backup_$$(date +%Y%m%d_%H%M%S).sql;
        find /backups -name '*.sql' -mtime +7 -delete;
        sleep 86400;
      done"
    environment:
      PGPASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - ./backups:/backups
    profiles: [backup]
```

---

## Common Patterns

### Pattern 1: Database with Persistent Volume

```yaml
services:
  db:
    image: postgres:16
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro

volumes:
  pgdata: {}  # Persists across container restarts
```

### Pattern 2: Shared Volume Between Services

```yaml
services:
  builder:
    image: node:20
    command: npm run build
    volumes:
      - build_output:/app/dist   # Write built files

  nginx:
    image: nginx
    volumes:
      - build_output:/usr/share/nginx/html:ro  # Serve built files

volumes:
  build_output: {}
```

### Pattern 3: Dev vs Prod Volumes

```yaml
# docker-compose.yml (base)
services:
  app:
    volumes:
      - app_data:/app/data

# docker-compose.override.yml (dev — auto-loaded)
services:
  app:
    volumes:
      - .:/app              # Live code
      - /app/node_modules   # Exclude node_modules

# docker-compose.prod.yml
services:
  app:
    volumes:
      - app_data:/app/data
      # No bind mounts in prod!
```

### Pattern 4: Secrets via tmpfs

```yaml
services:
  app:
    secrets:
      - db_password
    volumes:
      - type: tmpfs
        target: /tmp/secrets

secrets:
  db_password:
    file: ./secrets/db_password.txt
    # Mounted at: /run/secrets/db_password
```

---

## Volume Troubleshooting

```bash
# Find volume location on host
docker volume inspect mydata
# Look for "Mountpoint": "/var/lib/docker/volumes/mydata/_data"

# Check what's in a volume
docker run --rm -v mydata:/data alpine ls -la /data

# Fix permission issues
docker run --rm -v mydata:/data alpine chown -R 1000:1000 /data

# Check which containers use a volume
docker ps --filter volume=mydata

# Dangling volumes (no container using them)
docker volume ls -f dangling=true
docker volume prune  # Remove them
```

---

**Next:** [Multi-Stage Builds →](../06_multi_stage/multi_stage_guide.md)
