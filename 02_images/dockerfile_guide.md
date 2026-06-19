# 🐳 Module 02 — Dockerfile Deep Dive

> **Level:** 🟡 Intermediate | **Time:** ~3 hours | **Prerequisites:** Module 01

---

## 📖 Table of Contents

- [Dockerfile Anatomy](#dockerfile-anatomy)
- [All Instructions Reference](#all-instructions-reference)
- [Layer Caching Strategy](#layer-caching-strategy)
- [ARG vs ENV](#arg-vs-env)
- [COPY vs ADD](#copy-vs-add)
- [CMD vs ENTRYPOINT](#cmd-vs-entrypoint)
- [Real-World Examples](#real-world-examples)
- [.dockerignore](#dockerignore)

---

## Dockerfile Anatomy

```
# ┌──────────────────────────────────────────────────────────┐
# │                   Dockerfile Structure                    │
# └──────────────────────────────────────────────────────────┘

# 1. Syntax directive (optional, must be FIRST)
# syntax=docker/dockerfile:1

# 2. Base image (REQUIRED — always first instruction)
FROM node:20-alpine

# 3. Metadata
LABEL maintainer="dev@example.com"
LABEL version="2.1.0"

# 4. Build arguments (overridable at build time)
ARG NODE_ENV=production

# 5. Environment variables (available at runtime)
ENV PORT=3000

# 6. Work directory
WORKDIR /app

# 7. Copy files (order matters for cache!)
COPY package*.json ./
RUN npm ci --only=production

COPY . .

# 8. Build the application
RUN npm run build

# 9. Runtime configuration
EXPOSE 3000
USER node

# 10. Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -qO- http://localhost:3000/health || exit 1

# 11. Default command
CMD ["node", "dist/server.js"]
```

---

## All Instructions Reference

### `FROM` — Base Image

```dockerfile
FROM ubuntu:22.04                  # Specific version (ALWAYS pin!)
FROM ubuntu:22.04 AS builder       # Named stage for multi-stage builds
FROM scratch                       # Empty base (for tiny binaries)

# ⚠️  NEVER use "FROM ubuntu" (latest changes and breaks builds)
# ✅  ALWAYS pin: "FROM ubuntu:22.04"
```

### `RUN` — Execute Commands

```dockerfile
# Shell form (runs in /bin/sh -c)
RUN apt-get update && apt-get install -y curl

# Exec form (no shell, no variable substitution)
RUN ["apt-get", "install", "-y", "curl"]

# Best practice: Chain && to minimize layers
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
       git \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*   # Clean apt cache!
#                                      ↑ Crucial for small images!
```

### `COPY` — Copy Files

```dockerfile
COPY src dst                       # Copy file or directory
COPY . .                           # Copy all (respect .dockerignore!)
COPY --chown=node:node . .         # Copy with ownership
COPY --from=builder /app/dist .    # Copy from another stage
COPY ["src file", "dst dir/"]      # Exec form (handles spaces)
```

### `ADD` — Advanced Copy (use sparingly)

```dockerfile
ADD archive.tar.gz /app/           # Auto-extract tar archives
ADD https://example.com/file.txt . # Download URL (prefer curl/wget)

# ⚠️  Prefer COPY unless you need tar auto-extraction
```

### `WORKDIR` — Set Working Directory

```dockerfile
WORKDIR /app                       # Create and switch to /app
WORKDIR /app/src                   # Relative paths are relative to last WORKDIR
# Equivalent to: mkdir -p /app && cd /app — but better!
```

### `ENV` — Environment Variables

```dockerfile
ENV PORT=3000                      # Single variable
ENV NODE_ENV=production \          # Multiple (legacy syntax)
    LOG_LEVEL=info
ENV PORT=3000 NODE_ENV=production  # Modern syntax

# Available at BOTH build-time (after this line) AND runtime
```

### `ARG` — Build Arguments

```dockerfile
ARG VERSION=latest                 # Default value
ARG BUILD_DATE                     # No default (required)

# Pass at build time:
# docker build --build-arg VERSION=1.2.3 .

# ⚠️  ARG values are NOT available at runtime (unlike ENV)
# ⚠️  ARG values appear in docker history — don't use for secrets!
```

### `EXPOSE` — Document Ports

```dockerfile
EXPOSE 3000         # TCP (default)
EXPOSE 8080/tcp     # Explicit TCP
EXPOSE 5353/udp     # UDP

# ⚠️  This is DOCUMENTATION only — doesn't actually publish ports!
# Use: docker run -p 3000:3000  to actually expose
```

### `USER` — Switch User

```dockerfile
# Create non-root user and switch to it
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid appuser --shell /bin/bash appuser
USER appuser

# Or use existing system user
USER node        # For node images
USER www-data    # For web server images

# ✅  Always run as non-root in production!
```

### `VOLUME` — Declare Mount Points

```dockerfile
VOLUME ["/data"]           # Exec form (preferred)
VOLUME /data /logs         # Multiple volumes

# Creates an anonymous volume — better to manage volumes explicitly
```

### `HEALTHCHECK` — Container Health

```dockerfile
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=5s \
            --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Exit codes: 0 = healthy, 1 = unhealthy
# Disable inherited healthcheck:
HEALTHCHECK NONE
```

### `CMD` vs `ENTRYPOINT`

```dockerfile
# CMD — Default command (easily overridden)
CMD ["node", "server.js"]             # Exec form (preferred)
CMD node server.js                    # Shell form

# ENTRYPOINT — Fixed executable (arguments appended)
ENTRYPOINT ["docker-entrypoint.sh"]   # Script as entrypoint
ENTRYPOINT ["node"]

# Combination pattern:
ENTRYPOINT ["node"]
CMD ["server.js"]    # docker run myapp → node server.js
                     # docker run myapp other.js → node other.js
```

### `ONBUILD` — Trigger for Downstream Images

```dockerfile
ONBUILD COPY . /app
ONBUILD RUN npm install

# Triggers execute when this image is used as a base
# Useful for base images that need child content
```

### `STOPSIGNAL` — Override Stop Signal

```dockerfile
STOPSIGNAL SIGTERM    # Default
STOPSIGNAL SIGQUIT    # Graceful quit for some apps
STOPSIGNAL 9          # SIGKILL (force)
```

---

## Layer Caching Strategy

```
Build Order (WRONG ❌)          Build Order (RIGHT ✅)
────────────────────            ──────────────────────

FROM node:20                    FROM node:20

COPY . .          ← COPY ALL   WORKDIR /app
                    FIRST
RUN npm install   ← Cache MISS  COPY package*.json ./  ← Only pkg files
                    on every      (rarely changes)
                    code change  RUN npm install        ← Cached! ✅

                                COPY . .               ← Code changes
                                                         here (fast!)

 Result: npm install runs         Result: npm install only
 EVERY single build!              runs when package.json changes
```

### Cache Invalidation Rules

```
Layer N changes → ALL subsequent layers are REBUILT

FROM ubuntu:22.04             # Layer 1 — rarely changes
RUN apt-get update            # Layer 2 — rebuild if L1 changes
RUN apt-get install -y curl   # Layer 3 — rebuild if L2 changes
COPY package.json .           # Layer 4 — changes when pkg.json changes
RUN npm install               # Layer 5 — only rebuild if L4 changes
COPY . .                      # Layer 6 — changes on every code edit
RUN npm run build             # Layer 7 — rebuilt only when code changes

 Principle: Put STABLE things FIRST, CHANGING things LAST
```

---

## ARG vs ENV

```
              ARG                    ENV
              ───                    ───
Available:    Build-time only    Both build & runtime
Override:     --build-arg        -e / --env-file
In history:   Yes (⚠️ visible)   Yes (⚠️ visible)
Default:      Optional           Optional
Use for:      Build config       App configuration
Secrets:      ❌ Never            ❌ Never (use secrets!)
```

```dockerfile
# Pattern: ARG to ENV bridge
ARG APP_VERSION=1.0.0
ENV APP_VERSION=${APP_VERSION}
# Now available at runtime too!
```

---

## CMD vs ENTRYPOINT

```
                     CMD                    ENTRYPOINT
                     ───                    ──────────
Overridden by:       docker run <image> CMD  --entrypoint flag
Append args:         No (replaces CMD)       Yes (appends to ENTRYPOINT)
Shell form:          Yes                     Yes
Exec form:           Yes (preferred)         Yes (preferred)
Best use:            Default arguments        Fixed executable
```

```
Dockerfile:           docker run command:       Actual execution:
─────────────────     ────────────────────      ──────────────────
CMD ["ping","8.8.8.8"]  (none)                ping 8.8.8.8
CMD ["ping","8.8.8.8"]  curl google.com        curl google.com  ← replaced

ENTRYPOINT ["ping"]     (none)                 ping (no args, error)
ENTRYPOINT ["ping"]     8.8.8.8               ping 8.8.8.8  ← appended
ENTRYPOINT ["ping"]     --entrypoint curl ...  curl (override)

ENTRYPOINT ["ping"]     (none)                 ping 8.8.8.8
CMD ["8.8.8.8"]
```

---

## Real-World Examples

### Node.js Application

```dockerfile
# syntax=docker/dockerfile:1
FROM node:20-alpine AS base

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# ── Dependencies stage ──────────────────────────────────────
FROM base AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# ── Build stage ─────────────────────────────────────────────
FROM base AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# ── Production stage ─────────────────────────────────────────
FROM base AS production
WORKDIR /app
ENV NODE_ENV=production

# Copy production deps and built files
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./

# Non-root user
USER node
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s \
  CMD wget -qO- http://localhost:3000/health || exit 1

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/server.js"]
```

### Python/FastAPI Application

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ── Builder ─────────────────────────────────────────────────
FROM base AS builder
WORKDIR /app

RUN pip install poetry==1.7.1
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# ── Production ──────────────────────────────────────────────
FROM base AS production
WORKDIR /app

RUN addgroup --system app && adduser --system --group app

COPY --from=builder /app/requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=app:app . .

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## .dockerignore

```
# .dockerignore — prevents sending unnecessary files to build context

# Version control
.git
.gitignore
.gitattributes

# Node.js
node_modules
npm-debug.log
.npm

# Python
__pycache__
*.py[cod]
.venv
venv/
*.egg-info/

# Build artifacts
dist/
build/
*.o
*.a

# Test files
coverage/
*.test.js
*.spec.js
__tests__/

# Documentation
*.md
docs/

# Docker files (not needed inside image)
Dockerfile*
docker-compose*
.dockerignore

# OS files
.DS_Store
Thumbs.db

# Environment files (NEVER include!)
.env
.env.*
*.env
secrets/
```

---

**Next:** [Docker Compose Guide →](../03_compose/compose_guide.md)
