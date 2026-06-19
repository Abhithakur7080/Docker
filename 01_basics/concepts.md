# 🐳 Module 01 — Docker Core Concepts

> **Level:** 🟢 Beginner | **Time:** ~2 hours | **Prerequisites:** None

---

## 📖 Table of Contents

- [What is Docker?](#what-is-docker)
- [The Problem Docker Solves](#the-problem-docker-solves)
- [Containers vs Virtual Machines](#containers-vs-virtual-machines)
- [Docker Architecture](#docker-architecture)
- [Core Objects](#core-objects)
- [Container Lifecycle](#container-lifecycle)
- [Namespaces & cgroups](#namespaces--cgroups)

---

## What is Docker?

Docker is an **open-source platform** for developing, shipping, and running applications in isolated environments called **containers**.

```
WITHOUT DOCKER                    WITH DOCKER
─────────────                     ───────────
"It works on my machine!"    →    Works EVERYWHERE ✅
Dependency conflicts         →    Isolated dependencies ✅
Complex setup docs           →    docker run <image> ✅
Slow VM provisioning         →    Start in milliseconds ✅
```

---

## The Problem Docker Solves

### 🔴 Before Docker (The Matrix of Hell)

```
                 Dev     Test    Staging  Production
                 ────    ────    ───────  ──────────
Node.js 14.x     ✅      ❌        ✅        ❌
Python 3.8       ✅      ✅        ❌        ✅
MySQL 5.7        ❌      ✅        ✅        ❌
Redis 6.x        ✅      ❌        ❌        ✅

Result: "Dependency Hell" 😱
```

### ✅ After Docker

```
Container A            Container B            Container C
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│ Node.js 14  │        │ Python 3.11 │        │ Java 17     │
│ MySQL 5.7   │        │ PostgreSQL  │        │ Redis 7.x   │
│ Redis 6.x   │        │ MongoDB     │        │ Nginx       │
└─────────────┘        └─────────────┘        └─────────────┘
      Same host, zero conflicts! 🎉
```

---

## Containers vs Virtual Machines

```
VIRTUAL MACHINE (VM)              DOCKER CONTAINER
────────────────────              ────────────────
┌────────────────────┐            ┌────────────────────┐
│      App A         │            │      App A         │
│  ┌─────────────┐   │            │  ┌─────────────┐   │
│  │   Bins/Libs │   │            │  │   Bins/Libs │   │
│  └─────────────┘   │            │  └─────────────┘   │
│  ┌─────────────┐   │            └──────────┬─────────┘
│  │  Guest OS   │   │                       │
│  │ (2-4 GB!)   │   │            ┌──────────▼─────────┐
│  └─────────────┘   │            │   Container Engine  │
│  ┌─────────────┐   │            │   (Docker Daemon)   │
│  │  Hypervisor │   │            └──────────┬─────────┘
│  └─────────────┘   │                       │
└────────────────────┘            ┌──────────▼─────────┐
                                  │   HOST OS KERNEL    │
                                  └──────────┬─────────┘
       Heavy (GBs)                           │
       Slow boot (minutes)            ┌──────▼──────┐
       Full OS overhead               │   Hardware  │
                                      └─────────────┘
                                  Lightweight (MBs)
                                  Fast boot (seconds)
                                  Shared kernel
```

### Comparison Table

| Feature           | Virtual Machine    | Docker Container  |
|-------------------|--------------------|-------------------|
| **Size**          | GB range           | MB range          |
| **Boot Time**     | Minutes            | Seconds           |
| **OS**            | Full Guest OS      | Shared Host Kernel|
| **Isolation**     | Strong             | Process-level     |
| **Portability**   | Moderate           | Excellent         |
| **Performance**   | Near-native        | Native            |
| **Density**       | ~10s per host      | 100s per host     |

---

## Docker Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT                                  │
│  docker build  docker pull  docker run  docker-compose up       │
└───────────────────────────────┬─────────────────────────────────┘
                                │ REST API (unix socket / TCP)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DOCKER DAEMON (dockerd)                    │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐   │
│  │  Image Mgmt │  │ Container   │  │   Network / Volume   │   │
│  │  Build/Pull │  │ Lifecycle   │  │   Management         │   │
│  └──────┬──────┘  └──────┬──────┘  └──────────────────────┘   │
│         │                │                                      │
│         ▼                ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    containerd                           │   │
│  │         (Industry-standard container runtime)           │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│                          │                                      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  runc / crun                            │   │
│  │           (OCI-compliant low-level runtime)             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       REGISTRY                                  │
│              Docker Hub / GitHub Container Registry             │
│              AWS ECR / Google GCR / Self-hosted                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Objects

### 🖼️ Images

```
Image = Read-only template + metadata

┌─────────────────────────────────────────┐
│              ubuntu:22.04               │
├─────────────────────────────────────────┤
│  Layer 4: RUN apt install python3  (8MB)│  ← Your layer
├─────────────────────────────────────────┤
│  Layer 3: RUN apt update          (12MB)│  ← Your layer
├─────────────────────────────────────────┤
│  Layer 2: ENV DEBIAN_FRONTEND...   (0KB)│  ← Base layer
├─────────────────────────────────────────┤
│  Layer 1: Base OS filesystem      (77MB)│  ← Base layer
└─────────────────────────────────────────┘
         All layers are IMMUTABLE
```

### 📦 Containers

```
Container = Image (read-only) + Writable Layer + Runtime config

┌─────────────────────────────────────────┐
│    🔵 WRITABLE LAYER (Container Layer)  │ ← Created at runtime
├─────────────────────────────────────────┤ ← Removed when container stops
│    🔒 Image Layer 3 (read-only)         │
├─────────────────────────────────────────┤
│    🔒 Image Layer 2 (read-only)         │
├─────────────────────────────────────────┤
│    🔒 Image Layer 1 (read-only)         │
└─────────────────────────────────────────┘
```

---

## Container Lifecycle

```
                    docker create
                         │
               ┌─────────▼──────────┐
               │      CREATED       │
               └─────────┬──────────┘
                         │ docker start
               ┌─────────▼──────────┐
          ┌───▶│      RUNNING       │◀──┐
          │    └──┬──────────┬──────┘   │
          │       │          │          │
    docker│  docker│    docker│     docker│
    unpause│  pause│    stop  │     start │
          │       │          │          │
          │    ┌──▼──┐  ┌────▼─────┐   │
          └────│PAUSE│  │ STOPPED  │───┘
               └─────┘  └────┬─────┘
                             │ docker rm
               ┌─────────────▼──────────┐
               │        REMOVED         │
               └────────────────────────┘

States: created → running → paused → stopped → removed
```

---

## Namespaces & cgroups

Docker uses Linux kernel features for isolation:

### 🔐 Namespaces (Isolation)

```
┌─────────────────────────────────────────────────────┐
│                 NAMESPACES                          │
├──────────────┬──────────────────────────────────────┤
│  PID         │ Process IDs (own process tree)        │
│  NET         │ Network interfaces, routes, ports     │
│  MNT         │ Filesystem mount points               │
│  UTS         │ Hostname and domain name              │
│  IPC         │ Shared memory, semaphores             │
│  USER        │ User/group IDs                        │
│  CGROUP      │ cgroup root directory (Linux 4.6+)    │
└──────────────┴──────────────────────────────────────┘
```

### ⚙️ cgroups (Resource Control)

```
┌─────────────────────────────────────────────────────┐
│                 CGROUPS (Control Groups)             │
├──────────────┬──────────────────────────────────────┤
│  cpu         │ CPU time allocation & throttling      │
│  memory      │ Memory limits & OOM handling          │
│  blkio       │ Block I/O throttling                  │
│  net_cls     │ Network packet tagging                │
│  devices     │ Device access control                 │
│  pids        │ Process count limits                  │
└──────────────┴──────────────────────────────────────┘

Example:
  docker run --memory=512m --cpus=1.5 nginx
  └── Container can use max 512MB RAM & 1.5 CPU cores
```

---

## 📝 Key Takeaways

- ✅ Docker packages apps + dependencies into **portable containers**
- ✅ Containers share the host kernel — **lighter than VMs**
- ✅ Images are **immutable, layered** templates
- ✅ Containers are **ephemeral** by default (data lost on stop)
- ✅ Docker uses **namespaces** for isolation & **cgroups** for resource limits

---

**Next:** [Commands Cheatsheet →](./commands_cheatsheet.md)
