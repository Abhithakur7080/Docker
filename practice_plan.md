# 📋 Docker 4-Week Practice Plan

> **Goal:** Go from Docker beginner to production-ready in 4 structured weeks.
> Open `index.html` in your browser for the interactive version with progress tracking!

---

## 🗓️ Overview

```
┌──────────────┬──────────────────────────────────┬─────────┬──────────┐
│ Week         │ Modules                          │ Level   │ Est. Time│
├──────────────┼──────────────────────────────────┼─────────┼──────────┤
│ Week 1       │ Basics · Images · Compose        │ 🟢 Beg  │ ~14 hrs  │
│ Week 2       │ Networking · Storage · Multi-Stg │ 🟡 Int  │ ~11 hrs  │
│ Week 3       │ Security · Orchestration · CI/CD │ 🔴 Adv  │ ~16 hrs  │
│ Week 4       │ Production · Monitoring · Best   │ 🏆 Exp  │ ~15 hrs  │
└──────────────┴──────────────────────────────────┴─────────┴──────────┘
```

---

## 🟢 Week 1 — Foundation (Beginner)

**Theme:** Getting comfortable with Docker core fundamentals  
**Modules:** 01_basics · 02_images · 03_compose  
**Total Time:** ~14 hours

### Monday — Docker Basics: Core Concepts (95 min)
| Type | Task | Duration |
|------|------|----------|
| 📄 Read | `01_basics/concepts.md` — Core Docker concepts | 45 min |
| 🔨 Practice | Install Docker Desktop & run `docker run hello-world` | 30 min |
| 📄 Read | First 20 commands from `commands_cheatsheet.md` | 20 min |

### Tuesday — Docker Basics: CLI Mastery (135 min)
| Type | Task | Duration |
|------|------|----------|
| 📄 Read | Study full `01_basics/commands_cheatsheet.md` | 60 min |
| 🔨 Practice | Drill: `docker run`, `ps`, `stop`, `rm`, `images` | 45 min |
| 🏗️ Build | Build and run `01_basics/Dockerfile.hello` | 30 min |

### Wednesday — Docker Images: Dockerfiles (135 min)
| Type | Task | Duration |
|------|------|----------|
| 📄 Read | `02_images/dockerfile_guide.md` — all instructions | 60 min |
| 🏗️ Build | Write and build your first custom image | 45 min |
| 📄 Read | `02_images/image_layers.md` — caching strategy | 30 min |

### Thursday — Docker Images: Optimization (90 min)
| Type | Task | Duration |
|------|------|----------|
| 🏗️ Build | Build `Dockerfile.optimized` — compare sizes | 60 min |
| 🔨 Practice | `docker tag` + `docker push` to Docker Hub | 30 min |

### Friday — Docker Compose (125 min)
| Type | Task | Duration |
|------|------|----------|
| 📄 Read | `03_compose/compose_guide.md` — concepts & syntax | 60 min |
| 🔨 Practice | `docker compose up -d` — run the full-stack app | 45 min |
| 📄 Read | Study `docker-compose.prod.yml` override patterns | 20 min |

### Saturday — Week 1 Project & Consolidation (120 min)
| Type | Task | Duration |
|------|------|----------|
| 🏗️ Build | Add a Redis service to `docker-compose.yml` | 45 min |
| 🔨 Practice | `docker compose up --scale web=3` — test scaling | 30 min |
| 🔨 Practice | Week 1 self-quiz & review notes | 45 min |

### ✅ Week 1 Checkpoint
- [ ] Can explain the difference between image and container
- [ ] Can write a basic Dockerfile from scratch
- [ ] Can run a multi-container app with `docker compose up`
- [ ] Know how to use `docker run`, `ps`, `stop`, `rm`, `images`, `logs`

---

## 🟡 Week 2 — Intermediate

**Theme:** Networking, persistent storage, and build optimization  
**Modules:** 04_networking · 05_storage · 06_multi_stage  
**Total Time:** ~11 hours

### Monday — Container Networking (120 min)
| Type | Task | Duration |
|------|------|----------|
| 📄 Read | `04_networking/networking_guide.md` | 60 min |
| 🔨 Practice | `docker network create my-net` + connect containers | 30 min |
| 🔨 Practice | Ping containers by name — test DNS resolution | 30 min |

### Tuesday — Networking Deep Dive (75 min)
| Type | Task | Duration |
|------|------|----------|
| 🏗️ Build | Run `04_networking/docker-compose.yml` example | 45 min |
| 🔨 Practice | `docker network inspect` — read the full JSON | 30 min |

### Wednesday — Storage & Volumes (130 min)
| Type | Task | Duration |
|------|------|----------|
| 📄 Read | `05_storage/volumes_guide.md` — all storage types | 60 min |
| 🔨 Practice | `docker volume create mydata` + mount + test persistence | 40 min |
| 🔨 Practice | Bind mount a local directory — watch live reload | 30 min |

### Thursday — Storage Advanced (75 min)
| Type | Task | Duration |
|------|------|----------|
| 🏗️ Build | Run `05_storage/docker-compose.yml` — test persistence | 45 min |
| 🔨 Practice | Create a volume backup `.tar.gz` with `docker run` | 30 min |

### Friday — Multi-Stage Builds (110 min)
| Type | Task | Duration |
|------|------|----------|
| 📄 Read | `06_multi_stage/multi_stage_guide.md` | 45 min |
| 🏗️ Build | `docker build` the multi-stage `Dockerfile` | 45 min |
| 🔨 Practice | Compare image sizes: `docker images ls` | 20 min |

### Saturday — Week 2 Project (90 min)
| Type | Task | Duration |
|------|------|----------|
| 🏗️ Build | Add a `test` stage to `06_multi_stage/Dockerfile` | 60 min |
| 🔨 Practice | Week 2 review — networking & storage quiz | 30 min |

### ✅ Week 2 Checkpoint
- [ ] Can create and use custom Docker networks
- [ ] Understand the difference between volumes and bind mounts
- [ ] Can build a multi-stage Dockerfile with <50MB final image
- [ ] Can explain layer caching and why instruction order matters

---

## 🔴 Week 3 — Advanced

**Theme:** Security, orchestration, and CI/CD automation pipelines  
**Modules:** 07_security · 08_orchestration · 09_cicd  
**Total Time:** ~16 hours

### Monday — Container Security (125 min)
| Type | Task | Duration |
|------|------|----------|
| 📄 Read | `07_security/security_guide.md` — full guide | 60 min |
| 🏗️ Build | Build `07_security/Dockerfile.secure` | 45 min |
| 🔨 Practice | `docker run --user` — verify UID is non-zero | 20 min |

### Tuesday — Security Hardening (75 min)
| Type | Task | Duration |
|------|------|----------|
| 🔨 Practice | `trivy image <your-image>` — find vulnerabilities | 45 min |
| 🔨 Practice | `docker run --read-only` — test hardened container | 30 min |

### Wednesday — Docker Swarm (150 min)
| Type | Task | Duration |
|------|------|----------|
| 📄 Read | `08_orchestration/swarm_guide.md` | 60 min |
| 🔨 Practice | `docker swarm init` — become a manager node | 45 min |
| 🏗️ Build | `docker stack deploy` — deploy your first stack | 45 min |

### Thursday — Kubernetes Migration (105 min)
| Type | Task | Duration |
|------|------|----------|
| 📄 Read | `08_orchestration/k8s_migration.md` | 60 min |
| 🔨 Practice | `docker service scale web=3` — rolling update | 45 min |

### Friday — CI/CD Pipelines (135 min)
| Type | Task | Duration |
|------|------|----------|
| 📄 Read | `09_cicd/cicd_guide.md` — concepts & patterns | 45 min |
| 📄 Read | Study `09_cicd/github_actions.yml` | 30 min |
| 🏗️ Build | Create `.github/workflows/docker.yml` in your repo | 60 min |

### Saturday — CI/CD & Review (105 min)
| Type | Task | Duration |
|------|------|----------|
| 📄 Read | Study `09_cicd/gitlab_ci.yml` pipeline | 30 min |
| 🔨 Practice | Push a commit — watch the pipeline execute | 45 min |
| 🔨 Practice | Week 3 review — security & orchestration | 30 min |

### ✅ Week 3 Checkpoint
- [ ] Can build a hardened, non-root Dockerfile
- [ ] Can scan images for CVEs with Trivy
- [ ] Can deploy and scale a Docker Swarm stack
- [ ] Have a working GitHub Actions Docker pipeline

---

## 🏆 Week 4 — Production & Mastery

**Theme:** Production deployment, observability, and Docker mastery  
**Modules:** 10_production · 11_monitoring · 12_best_practices  
**Total Time:** ~15 hours

### Monday — Production Deployment (150 min)
| Type | Task | Duration |
|------|------|----------|
| 📄 Read | `10_production/production_guide.md` — full checklist | 60 min |
| 🏗️ Build | `docker compose -f docker-compose.prod.yml up` | 60 min |
| 🏗️ Build | Add `HEALTHCHECK` instructions to your Dockerfiles | 30 min |

### Tuesday — Production Reliability (80 min)
| Type | Task | Duration |
|------|------|----------|
| 🔨 Practice | Test `--restart=always` and `--restart=on-failure:5` | 40 min |
| 🔨 Practice | Apply `cpus` + `memory` limits via compose `deploy:` | 40 min |

### Wednesday — Monitoring & Observability (120 min)
| Type | Task | Duration |
|------|------|----------|
| 📄 Read | `11_monitoring/monitoring_guide.md` | 60 min |
| 🏗️ Build | Deploy the Prometheus + Grafana monitoring stack | 60 min |

### Thursday — Monitoring Deep Dive (105 min)
| Type | Task | Duration |
|------|------|----------|
| 🔨 Practice | Create a Grafana dashboard with CPU/memory panels | 60 min |
| 🏗️ Build | Configure Prometheus alerting rules | 45 min |

### Friday — Best Practices Mastery (120 min)
| Type | Task | Duration |
|------|------|----------|
| 📄 Read | `12_best_practices/best_practices.md` — read fully | 60 min |
| 🔨 Practice | Audit an existing Dockerfile against the checklist | 60 min |

### Saturday — 🎓 Graduation Day (150 min)
| Type | Task | Duration |
|------|------|----------|
| 🏗️ Build | Write your personal Docker code-review checklist | 60 min |
| 🏗️ Build | Refactor a compose stack applying all best practices | 60 min |
| 🔨 Practice | 🎓 Final review — celebrate completion! | 30 min |

### ✅ Week 4 Checkpoint
- [ ] Can deploy a production-grade compose stack with health checks
- [ ] Have Prometheus + Grafana monitoring running
- [ ] Can write a Docker security review checklist
- [ ] Understand all 12 modules and can explain them to others

---

## 🎯 Task Type Legend

| Icon | Type | Description |
|------|------|-------------|
| 📄 Read | **Read** | Study the provided markdown guide |
| 🔨 Practice | **Practice** | Run commands and experiment in your terminal |
| 🏗️ Build | **Build** | Create, build, or extend Docker artifacts |

---

## 💡 Tips for Success

1. **Track your progress** — Open `index.html` in your browser for the interactive LMS dashboard
2. **Daily habit** — Even 30 minutes a day builds a streak and reinforces concepts
3. **Take notes** — Use the Notes section in the LMS or a physical notebook
4. **Experiment freely** — Docker containers are disposable, try breaking things!
5. **Log your time** — The LMS has a time logger per module to track your investment

---

> 💡 **Open `index.html` in your browser** to track your progress interactively with checkboxes, XP points, streaks, and achievement badges!
