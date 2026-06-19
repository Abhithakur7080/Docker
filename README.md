# 🐳 Docker — Complete Learning Hub

> **From Zero to Production** — A structured, visual guide through the entire Docker ecosystem.

---

## 📚 Learning Path

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DOCKER LEARNING PATH                         │
├─────────────┬──────────────────┬──────────────────┬────────────────┤
│  BEGINNER   │   INTERMEDIATE   │    ADVANCED      │  PRODUCTION    │
│  ⭐ Week 1  │   ⭐⭐ Week 2-3 │  ⭐⭐⭐ Week 4  │  🏆 Ongoing  │
├─────────────┼──────────────────┼──────────────────┼────────────────┤
│ 01_basics   │ 04_networking    │ 07_security      │ 10_production  │
│ 02_images   │ 05_storage       │ 08_orchestration │ 11_monitoring  │
│ 03_compose  │ 06_multi_stage   │ 09_cicd          │ 12_best_prctcs │
└─────────────┴──────────────────┴──────────────────┴────────────────┘
```

---

## 📂 Repository Structure

```
docker/
│
├── 📄 README.md                    ← You are here
│
├── 01_basics/
│   ├── 📄 concepts.md              ← Core Docker concepts
│   ├── 📄 commands_cheatsheet.md   ← All CLI commands
│   └── 🐋 Dockerfile.hello         ← Your first Dockerfile
│
├── 02_images/
│   ├── 📄 dockerfile_guide.md      ← Dockerfile deep dive
│   ├── 🐋 Dockerfile.optimized     ← Multi-stage build example
│   └── 📄 image_layers.md          ← Layer caching strategy
│
├── 03_compose/
│   ├── 📄 compose_guide.md         ← Docker Compose explained
│   ├── 🐋 docker-compose.yml       ← Full-stack example
│   └── 🐋 docker-compose.prod.yml  ← Production overrides
│
├── 04_networking/
│   ├── 📄 networking_guide.md      ← Network deep dive
│   └── 🐋 docker-compose.yml       ← Network examples
│
├── 05_storage/
│   ├── 📄 volumes_guide.md         ← Volumes & bind mounts
│   └── 🐋 docker-compose.yml       ← Storage examples
│
├── 06_multi_stage/
│   ├── 📄 multi_stage_guide.md     ← Build optimization
│   └── 🐋 Dockerfile               ← Real-world multi-stage
│
├── 07_security/
│   ├── 📄 security_guide.md        ← Hardening containers
│   └── 🐋 Dockerfile.secure        ← Security best practices
│
├── 08_orchestration/
│   ├── 📄 swarm_guide.md           ← Docker Swarm
│   └── 📄 k8s_migration.md         ← Moving to Kubernetes
│
├── 09_cicd/
│   ├── 📄 cicd_guide.md            ← CI/CD integration
│   ├── 📄 github_actions.yml       ← GitHub Actions workflow
│   └── 📄 gitlab_ci.yml            ← GitLab CI pipeline
│
├── 10_production/
│   ├── 📄 production_guide.md      ← Production checklist
│   └── 🐋 docker-compose.prod.yml  ← Full production stack
│
├── 11_monitoring/
│   ├── 📄 monitoring_guide.md      ← Observability stack
│   └── 🐋 docker-compose.yml       ← Prometheus + Grafana
│
└── 12_best_practices/
    └── 📄 best_practices.md        ← Master reference guide
```

---

## 🚀 Quick Start

```bash
# 1. Verify Docker installation
docker --version
docker compose version

# 2. Run your first container
docker run hello-world

# 3. Run an interactive Ubuntu container
docker run -it --rm ubuntu bash

# 4. Run nginx web server
docker run -d -p 8080:80 --name my-nginx nginx
# Open http://localhost:8080

# 5. List running containers
docker ps

# 6. Stop & remove
docker stop my-nginx && docker rm my-nginx
```

---

## 🗺️ Docker Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                        HOST MACHINE                                │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     DOCKER ENGINE                            │  │
│  │                                                              │  │
│  │  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐  │  │
│  │  │  Docker CLI  │──▶│ Docker Daemon│──▶│  containerd    │  │  │
│  │  │  (client)    │   │  (dockerd)   │   │  (runtime)     │  │  │
│  │  └──────────────┘   └──────────────┘   └────────────────┘  │  │
│  │           │                 │                   │            │  │
│  │           ▼                 ▼                   ▼            │  │
│  │  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐  │  │
│  │  │  Docker Hub  │   │   Images     │   │  Containers    │  │  │
│  │  │  (Registry)  │   │  (Read-only) │   │  (R/W layer)   │  │  │
│  │  └──────────────┘   └──────────────┘   └────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Volumes    │  │  Networks    │  │   Bind Mounts            │  │
│  │  (Persist)  │  │  (Isolate)   │  │   (Host paths)           │  │
│  └─────────────┘  └──────────────┘  └──────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Key Concepts at a Glance

| Concept        | Description                              | Analogy                    |
|----------------|------------------------------------------|----------------------------|
| **Image**      | Read-only template with instructions     | 📦 Shipping container spec |
| **Container**  | Running instance of an image             | 🚢 Actual container        |
| **Dockerfile** | Script to build an image                 | 📋 Recipe/Blueprint        |
| **Registry**   | Image storage & distribution server     | 🏪 App Store               |
| **Volume**     | Persistent data storage                  | 💾 External hard drive     |
| **Network**    | Communication channel between containers | 🌐 Private intranet        |
| **Compose**    | Multi-container orchestration tool       | 🎼 Orchestra conductor     |

---

## 🔗 Navigation

| Level | Topics | Files |
|-------|--------|-------|
| 🟢 Beginner | Concepts, CLI, First Dockerfile | [01_basics](./01_basics/concepts.md) |
| 🟡 Intermediate | Images, Compose, Networks, Storage | [02_images](./02_images/dockerfile_guide.md) |
| 🔴 Advanced | Security, Orchestration, CI/CD | [07_security](./07_security/security_guide.md) |
| 🏆 Expert | Production, Monitoring, Best Practices | [10_production](./10_production/production_guide.md) |

---

> 💡 **Tip:** Star ⭐ this repo and work through each module sequentially for the best learning experience.
