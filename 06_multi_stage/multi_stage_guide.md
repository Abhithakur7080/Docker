# 🐳 Module 06 — Multi-Stage Builds

> **Level:** 🟡 Intermediate | **Time:** ~2 hours | **Prerequisites:** Module 02

---

## 📖 Table of Contents

- [Why Multi-Stage Builds?](#why-multi-stage-builds)
- [Basic Multi-Stage Pattern](#basic-multi-stage-pattern)
- [Build Arguments & Targets](#build-arguments--targets)
- [Language-Specific Patterns](#language-specific-patterns)
- [BuildKit Features](#buildkit-features)
- [Image Size Comparison](#image-size-comparison)

---

## Why Multi-Stage Builds?

```
SINGLE STAGE (naive):                MULTI-STAGE (optimized):
──────────────────────               ─────────────────────────────

FROM node:20                         FROM node:20 AS builder
                                       RUN npm ci
RUN npm ci                             RUN npm run build
RUN npm run build                      RUN npm run test
RUN npm run test
                                     FROM node:20-alpine
# Final image contains:              COPY --from=builder /dist .
# ❌ All dev dependencies             # Final image contains:
# ❌ Test frameworks                  # ✅ Only production artifacts
# ❌ Build tools                      # ✅ No dev deps
# ❌ Source maps                      # ✅ No build tools
# ❌ TypeScript compiler              # ✅ No source code!
# ❌ Jest, Mocha, etc.
#
# Size: ~800MB                        # Size: ~80MB  (10x smaller!)
```

---

## Basic Multi-Stage Pattern

```dockerfile
# syntax=docker/dockerfile:1

# ──────────────────────────────────────────────────────────────
# STAGE 1: Base — shared config
# ──────────────────────────────────────────────────────────────
FROM node:20-alpine AS base

WORKDIR /app
ENV NODE_ENV=production

# ──────────────────────────────────────────────────────────────
# STAGE 2: Dependencies — install all deps
# ──────────────────────────────────────────────────────────────
FROM base AS deps

COPY package*.json ./
RUN npm ci                            # Install ALL deps (includes dev)

# ──────────────────────────────────────────────────────────────
# STAGE 3: Build — compile TypeScript, etc.
# ──────────────────────────────────────────────────────────────
FROM deps AS builder

COPY . .
RUN npm run build                     # Build output goes to /app/dist

# ──────────────────────────────────────────────────────────────
# STAGE 4: Test — run tests in CI
# ──────────────────────────────────────────────────────────────
FROM deps AS test

COPY . .
RUN npm test                          # Run tests before shipping!
# If tests fail, build fails here ← Great for CI!

# ──────────────────────────────────────────────────────────────
# STAGE 5: Production deps only
# ──────────────────────────────────────────────────────────────
FROM base AS prod-deps

COPY package*.json ./
RUN npm ci --only=production          # Only production deps

# ──────────────────────────────────────────────────────────────
# STAGE 6: Final — minimal production image ← DEFAULT TARGET
# ──────────────────────────────────────────────────────────────
FROM base AS production

# Copy ONLY what we need from previous stages
COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY package.json ./

# Security: non-root user
USER node

EXPOSE 3000
CMD ["node", "dist/server.js"]
```

### Building Specific Stages

```bash
# Build final (production) stage — default
docker build -t myapp:prod .

# Build only the test stage (for CI)
docker build --target test -t myapp:test .

# Build for development with all tools
docker build --target deps -t myapp:dev .
```

---

## Build Arguments & Targets

```dockerfile
# syntax=docker/dockerfile:1
FROM node:20-alpine AS base

ARG BUILD_ENV=production             # Controls which stage is used

# ── Development ──────────────────────────────────────────────────────────────
FROM base AS development

WORKDIR /app
COPY package*.json ./
RUN npm install                      # All deps including dev
COPY . .
CMD ["npm", "run", "dev"]

# ── Staging ──────────────────────────────────────────────────────────────────
FROM base AS staging

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
CMD ["node", "dist/server.js"]

# ── Production ────────────────────────────────────────────────────────────────
FROM node:20-alpine AS production

WORKDIR /app
ENV NODE_ENV=production

COPY --from=staging /app/dist ./dist
COPY --from=staging /app/node_modules ./node_modules
COPY package.json .

USER node
CMD ["node", "dist/server.js"]
```

```bash
# Target-based builds:
docker build --target development -t myapp:dev .
docker build --target staging -t myapp:staging .
docker build --target production -t myapp:prod .
```

---

## Language-Specific Patterns

### Go — Static Binary

```dockerfile
# syntax=docker/dockerfile:1

# ── Builder ───────────────────────────────────────────────────────────────────
FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download && go mod verify

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build \
    -ldflags='-w -s -extldflags "-static"' \
    -a -installsuffix cgo \
    -o /app/server ./cmd/server

# ── Final: SCRATCH (literally empty!) ────────────────────────────────────────
FROM scratch

# Copy SSL certs (scratch has none)
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /app/server /server

EXPOSE 8080
ENTRYPOINT ["/server"]

# Final image size: ~5-15MB vs 300MB+ for full Go image!
```

### Python — Virtual Environment

```dockerfile
# syntax=docker/dockerfile:1

# ── Builder ───────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN pip install poetry==1.7.1

# Install dependencies to venv
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --only=main --no-root

# ── Final ─────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS production

WORKDIR /app

# Create non-root user
RUN addgroup --system app && adduser --system --group app

# Copy only the virtual environment and app code
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app . .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

USER app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Java / Spring Boot — Layered JAR

```dockerfile
# syntax=docker/dockerfile:1

# ── Builder ───────────────────────────────────────────────────────────────────
FROM eclipse-temurin:21-jdk-alpine AS builder

WORKDIR /app
COPY mvnw pom.xml ./
COPY .mvn .mvn

# Download dependencies first (cache layer!)
RUN ./mvnw dependency:go-offline -B

COPY src ./src
RUN ./mvnw package -DskipTests && \
    java -Djarmode=layertools -jar target/*.jar extract

# ── Final ─────────────────────────────────────────────────────────────────────
FROM eclipse-temurin:21-jre-alpine AS production

WORKDIR /app

# Spring Boot layered JAR — only what changed gets rebuilt!
COPY --from=builder /app/dependencies/ ./
COPY --from=builder /app/spring-boot-loader/ ./
COPY --from=builder /app/snapshot-dependencies/ ./
COPY --from=builder /app/application/ ./

USER 1001
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s \
  CMD wget -qO- http://localhost:8080/actuator/health || exit 1

ENTRYPOINT ["java", "org.springframework.boot.loader.JarLauncher"]
```

### React Frontend — Nginx Serve

```dockerfile
# syntax=docker/dockerfile:1

# ── Build ─────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# ── Final ─────────────────────────────────────────────────────────────────────
FROM nginx:1.25-alpine AS production

# Custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built static files
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## BuildKit Features

```bash
# Enable BuildKit (default in Docker Desktop, enable on Linux):
export DOCKER_BUILDKIT=1
# Or add to /etc/docker/daemon.json:
# { "features": { "buildkit": true } }

# ── Cache Mounts ─────────────────────────────────────────────────────────────
RUN --mount=type=cache,target=/root/.npm \
    npm ci                           # npm cache persists between builds!

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt  # pip cache persists!

RUN --mount=type=cache,target=/root/.m2 \
    mvn package                      # Maven cache persists!

# ── Secret Mounts (never in image layers!) ────────────────────────────────────
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm install @private/package     # .npmrc used but NOT stored!

# Build with secret:
# echo "//registry.npmjs.org/:_authToken=TOKEN" > .npmrc
# docker build --secret id=npmrc,src=.npmrc .

# ── SSH Agent Forwarding ──────────────────────────────────────────────────────
RUN --mount=type=ssh \
    git clone git@github.com:org/private-repo.git  # Uses SSH agent!

# Build with SSH:
# docker build --ssh default .
```

---

## Image Size Comparison

```
IMAGE SIZE EXAMPLES (Node.js App):
────────────────────────────────────────────────────────────────────

Strategy                    Base Image          Final Size
──────────────              ────────────        ──────────
❌ Single stage, node:20    node:20             ~950MB
❌ Single stage, node:slim  node:20-slim        ~350MB
✅ Multi-stage, alpine      node:20-alpine      ~120MB
✅ Multi-stage, distroless  gcr.io/distroless   ~80MB
✅ Go static binary         scratch             ~8MB

Dockerfile SIZE REDUCERS:
  - Use Alpine or slim base images
  - Multi-stage builds (remove build tools)
  - Chain RUN commands (fewer layers)
  - .dockerignore (reduce build context)
  - --no-install-recommends (apt)
  - npm ci --only=production
  - rm -rf /var/lib/apt/lists/* (apt cleanup)

Check image sizes:
  docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

Analyze layers:
  docker history myimage:latest
  # OR use dive tool:
  docker run -ti --rm -v /var/run/docker.sock:/var/run/docker.sock \
    wagoodman/dive:latest myimage:latest
```

---

**Next:** [Security Guide →](../07_security/security_guide.md)
