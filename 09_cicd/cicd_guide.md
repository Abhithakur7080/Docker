# 🚀 Module 09 — CI/CD with Docker

> **Level:** 🔴 Advanced | **Time:** ~3 hours | **Prerequisites:** Modules 01-07

---

## 📖 Table of Contents

- [CI/CD Pipeline Architecture](#cicd-pipeline-architecture)
- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Multi-Architecture Builds](#multi-architecture-builds)
- [Registry Strategies](#registry-strategies)
- [Image Tagging Strategy](#image-tagging-strategy)
- [Deployment Patterns](#deployment-patterns)

---

## CI/CD Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       CI/CD PIPELINE FLOW                               │
└─────────────────────────────────────────────────────────────────────────┘

   Code Push
      │
      ▼
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Lint   │───▶│  Build   │───▶│   Test   │───▶│   Scan   │───▶│  Push    │
│ & Check │    │  Image   │    │(Unit/Int)│    │ (Trivy)  │    │ Registry │
└─────────┘    └──────────┘    └──────────┘    └──────────┘    └─────────┬┘
                                                                          │
              ┌───────────────────────────────────────────────────────────┘
              │
              ▼
      ┌───────────────────────────────────────────────┐
      │              DEPLOYMENT TARGETS                │
      ├──────────────┬──────────────┬──────────────────┤
      │    Dev/PR    │   Staging    │   Production     │
      │  (PR branch) │  (main branch│  (release tag)   │
      │  Auto-deploy │  Auto-deploy │  Manual approval │
      └──────────────┴──────────────┴──────────────────┘
```

---

## GitHub Actions

### Complete CI/CD Workflow

```yaml
# .github/workflows/docker.yml
name: Docker CI/CD

on:
  push:
    branches: [main, develop]
    tags:
      - 'v*.*.*'
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ────────────────────────────────────────────────────────────────────
  # JOB 1: Lint and Validate
  # ────────────────────────────────────────────────────────────────────
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Lint Dockerfile
        uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: Dockerfile
          failure-threshold: warning

      - name: Validate docker-compose.yml
        run: docker compose config --quiet

  # ────────────────────────────────────────────────────────────────────
  # JOB 2: Build & Test
  # ────────────────────────────────────────────────────────────────────
  test:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build test image
        uses: docker/build-push-action@v5
        with:
          context: .
          target: test
          load: true
          tags: myapp:test
          cache-from: type=gha         # GitHub Actions cache
          cache-to: type=gha,mode=max

      - name: Run unit tests
        run: |
          docker run --rm \
            -e DB_HOST=postgres \
            -e DB_PORT=5432 \
            --network host \
            myapp:test npm test

      - name: Run integration tests
        run: |
          docker compose -f docker-compose.test.yml up \
            --abort-on-container-exit \
            --exit-code-from tests

  # ────────────────────────────────────────────────────────────────────
  # JOB 3: Security Scan
  # ────────────────────────────────────────────────────────────────────
  security-scan:
    runs-on: ubuntu-latest
    needs: test
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4

      - name: Build image for scanning
        uses: docker/build-push-action@v5
        with:
          context: .
          load: true
          tags: myapp:scan

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:scan
          format: sarif
          output: trivy-results.sarif
          severity: CRITICAL,HIGH
          exit-code: '1'           # Fail on HIGH/CRITICAL

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-results.sarif

  # ────────────────────────────────────────────────────────────────────
  # JOB 4: Build & Push Production Image
  # ────────────────────────────────────────────────────────────────────
  build-push:
    runs-on: ubuntu-latest
    needs: [test, security-scan]
    if: github.event_name != 'pull_request'
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up QEMU (multi-arch)
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log into GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=sha,prefix=sha-
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64    # Multi-arch!
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            BUILD_DATE=${{ fromJSON(steps.meta.outputs.json).labels['org.opencontainers.image.created'] }}
            VERSION=${{ fromJSON(steps.meta.outputs.json).labels['org.opencontainers.image.version'] }}

      - name: Sign image with Cosign
        uses: sigstore/cosign-installer@v3
        continue-on-error: true

  # ────────────────────────────────────────────────────────────────────
  # JOB 5: Deploy to Staging
  # ────────────────────────────────────────────────────────────────────
  deploy-staging:
    runs-on: ubuntu-latest
    needs: build-push
    if: github.ref == 'refs/heads/main'
    environment: staging

    steps:
      - name: Deploy to staging
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: ${{ secrets.STAGING_USER }}
          key: ${{ secrets.STAGING_SSH_KEY }}
          script: |
            cd /app
            echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
            docker compose pull
            docker compose up -d --remove-orphans
            docker system prune -f

  # ────────────────────────────────────────────────────────────────────
  # JOB 6: Deploy to Production (manual approval)
  # ────────────────────────────────────────────────────────────────────
  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    if: startsWith(github.ref, 'refs/tags/v')
    environment:
      name: production
      url: https://myapp.com

    steps:
      - name: Deploy to production
        run: echo "Deploy to production"
        # ... production deployment steps
```

---

## GitLab CI

```yaml
# .gitlab-ci.yml
image: docker:26-dind

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"
  IMAGE_NAME: $CI_REGISTRY_IMAGE
  IMAGE_TAG: $CI_COMMIT_SHA

services:
  - docker:26-dind

stages:
  - lint
  - build
  - test
  - scan
  - push
  - deploy

# ── Templates ─────────────────────────────────────────────────────────────────
.docker-login: &docker-login
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

# ── Lint ─────────────────────────────────────────────────────────────────────
hadolint:
  stage: lint
  image: hadolint/hadolint:latest-alpine
  script:
    - hadolint Dockerfile
  allow_failure: false

compose-validate:
  stage: lint
  script:
    - docker compose config --quiet

# ── Build ─────────────────────────────────────────────────────────────────────
build:
  stage: build
  <<: *docker-login
  script:
    - docker buildx create --use
    - docker buildx build
        --cache-from type=registry,ref=$IMAGE_NAME:cache
        --cache-to type=registry,ref=$IMAGE_NAME:cache,mode=max
        --tag $IMAGE_NAME:$IMAGE_TAG
        --load
        .
    - docker save $IMAGE_NAME:$IMAGE_TAG | gzip > image.tar.gz
  artifacts:
    paths:
      - image.tar.gz
    expire_in: 1 hour

# ── Test ──────────────────────────────────────────────────────────────────────
unit-tests:
  stage: test
  script:
    - docker load < image.tar.gz
    - docker run --rm $IMAGE_NAME:$IMAGE_TAG npm test
  coverage: '/Statements\s*:\s*([0-9.]+)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

integration-tests:
  stage: test
  script:
    - docker compose -f docker-compose.test.yml up
        --abort-on-container-exit
        --exit-code-from tests
  after_script:
    - docker compose -f docker-compose.test.yml down -v

# ── Security Scan ─────────────────────────────────────────────────────────────
trivy:
  stage: scan
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    - trivy image
        --exit-code 1
        --no-progress
        --severity CRITICAL,HIGH
        --format sarif
        --output trivy-report.sarif
        $IMAGE_NAME:$IMAGE_TAG
  artifacts:
    reports:
      sast: trivy-report.sarif
    when: always

# ── Push to Registry ──────────────────────────────────────────────────────────
push-branch:
  stage: push
  <<: *docker-login
  script:
    - docker load < image.tar.gz
    - docker tag $IMAGE_NAME:$IMAGE_TAG $IMAGE_NAME:$CI_COMMIT_BRANCH
    - docker push $IMAGE_NAME:$IMAGE_TAG
    - docker push $IMAGE_NAME:$CI_COMMIT_BRANCH
  only:
    - branches

push-tag:
  stage: push
  <<: *docker-login
  script:
    - docker load < image.tar.gz
    - docker tag $IMAGE_NAME:$IMAGE_TAG $IMAGE_NAME:$CI_COMMIT_TAG
    - docker tag $IMAGE_NAME:$IMAGE_TAG $IMAGE_NAME:latest
    - docker push $IMAGE_NAME:$CI_COMMIT_TAG
    - docker push $IMAGE_NAME:latest
  only:
    - tags

# ── Deploy ────────────────────────────────────────────────────────────────────
deploy-staging:
  stage: deploy
  environment:
    name: staging
    url: https://staging.myapp.com
  script:
    - apk add --no-cache openssh-client
    - mkdir -p ~/.ssh && chmod 700 ~/.ssh
    - echo "$STAGING_SSH_KEY" > ~/.ssh/id_rsa && chmod 600 ~/.ssh/id_rsa
    - ssh -o StrictHostKeyChecking=no $STAGING_USER@$STAGING_HOST
        "cd /app && docker compose pull && docker compose up -d"
  only:
    - main

deploy-production:
  stage: deploy
  environment:
    name: production
    url: https://myapp.com
  when: manual              # Requires manual trigger!
  script:
    - echo "Deploy to production"
  only:
    - tags
```

---

## Multi-Architecture Builds

```bash
# ── Setup Buildx for multi-arch ──────────────────────────────────────────────
docker buildx create --name mybuilder --use
docker buildx inspect --bootstrap

# List supported platforms:
docker buildx inspect mybuilder | grep Platforms

# Build for multiple platforms at once:
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --tag myrepo/myimage:latest \
  --push \
  .

# Build and load locally (single arch only):
docker buildx build \
  --platform linux/amd64 \
  --load \
  -t myimage:test \
  .
```

```yaml
# GitHub Actions multi-arch:
- name: Set up QEMU
  uses: docker/setup-qemu-action@v3

- name: Build multi-arch
  uses: docker/build-push-action@v5
  with:
    platforms: linux/amd64,linux/arm64
    push: true
    tags: myrepo/myimage:latest
```

---

## Image Tagging Strategy

```
TAGGING STRATEGY:
─────────────────────────────────────────────────────────────────────

Commit SHA:        myimage:sha-abc1234    ← Immutable, exact version
Branch:            myimage:main           ← Latest on branch (mutable)
Semver:            myimage:v2.1.3         ← Specific release
Semver minor:      myimage:v2.1           ← Latest patch
Semver major:      myimage:v2             ← Latest minor
Latest:            myimage:latest         ← Latest stable

PROMOTION FLOW:
────────────────────────────────────────────────────────────────────

PR merged to main:
  myimage:sha-abc1234    (immutable)
  myimage:main           (update)

Test passes on staging:
  myimage:sha-abc1234    (same)
  myimage:v2.1.3         (add tag)

Production approved:
  myimage:sha-abc1234    (same)
  myimage:v2.1           (update)
  myimage:v2             (update)
  myimage:latest         (update)

KEY PRINCIPLE: Never change SHA tag. Only add new tags to existing SHAs.
```

---

## Deployment Patterns

### Rolling Update (Zero Downtime)

```bash
# Docker Swarm rolling update
docker service update \
  --image myapp:v2.1.3 \
  --update-parallelism 1 \
  --update-delay 30s \
  --update-failure-action rollback \
  myapp_web
```

### Blue-Green Deployment

```
v1 (BLUE) is live → Deploy v2 (GREEN) → Test GREEN → Switch traffic → Keep BLUE as fallback

  Load Balancer
       │
  ┌────┴────┐
  │  BLUE   │ ← currently live
  │  v1.0   │
  └─────────┘

  ┌─────────┐
  │  GREEN  │ ← deploying v2
  │  v2.0   │
  └─────────┘

  After switch:
  Load Balancer → GREEN (v2.0 live)
  BLUE kept for fast rollback
```

```bash
# Simple blue-green with Compose
docker compose -p myapp-green -f docker-compose.yml up -d --build
# ... test green
# Switch nginx/LB to green
docker compose -p myapp-blue down  # Remove old blue
docker compose -p myapp-green rename myapp-blue  # Green becomes blue
```

---

**Next:** [Production Guide →](../10_production/production_guide.md)
