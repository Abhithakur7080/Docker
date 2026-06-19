# 🏆 Production Guide — Docker in Production

> **Level:** 🏆 Expert | **Time:** ~4 hours | **Prerequisites:** All previous modules

---

## 📖 Table of Contents

- [Production Checklist](#production-checklist)
- [High Availability Setup](#high-availability-setup)
- [Zero Downtime Deployments](#zero-downtime-deployments)
- [Backup Strategy](#backup-strategy)
- [Incident Response](#incident-response)
- [Performance Tuning](#performance-tuning)

---

## Production Checklist

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     PRE-PRODUCTION CHECKLIST                             │
└──────────────────────────────────────────────────────────────────────────┘

IMAGE & BUILD
─────────────────────────────────────────────────────────────────────────
[ ] All base image versions pinned (not :latest)
[ ] Multi-stage build used
[ ] Non-root user configured (USER instruction)
[ ] Image scanned for CVEs (Trivy/Snyk) — no HIGH/CRITICAL
[ ] .dockerignore exists and excludes secrets, dev files
[ ] Image size verified (< 200MB for most apps)
[ ] HEALTHCHECK defined
[ ] Graceful shutdown implemented (SIGTERM handler)
[ ] dumb-init or tini for PID 1

SECURITY
─────────────────────────────────────────────────────────────────────────
[ ] No secrets in Dockerfile, env vars, or image layers
[ ] Secrets managed via Docker secrets or vault
[ ] read_only: true on container filesystem
[ ] cap_drop: [ALL] + only required caps added
[ ] no-new-privileges: true
[ ] Memory and CPU limits set
[ ] Network segmented (DB not exposed to internet)
[ ] --privileged NEVER used
[ ] Docker socket not mounted in containers
[ ] TLS for all external traffic

RELIABILITY
─────────────────────────────────────────────────────────────────────────
[ ] restart: unless-stopped (or on-failure)
[ ] depends_on with health checks
[ ] Health checks on all services
[ ] Data in named volumes (not container layer)
[ ] Backup strategy tested
[ ] Disaster recovery documented and tested

OBSERVABILITY
─────────────────────────────────────────────────────────────────────────
[ ] Structured JSON logging
[ ] Log rotation configured (max-size, max-file)
[ ] Prometheus metrics exposed
[ ] Grafana dashboards configured
[ ] Alerts configured for: down, high CPU, high mem, disk
[ ] Distributed tracing (if microservices)

OPERATIONS
─────────────────────────────────────────────────────────────────────────
[ ] Deployment process documented
[ ] Rollback procedure tested
[ ] On-call runbook created
[ ] Database migration strategy defined
[ ] SSL certificates automated (Let's Encrypt)
[ ] DNS configured and tested
[ ] Load testing performed
[ ] Capacity planning done
```

---

## High Availability Setup

```
SINGLE HOST (Simple)          HIGH AVAILABILITY (Production)
────────────────────           ───────────────────────────────────

   ┌──────────┐                Load Balancer (HAProxy/AWS ALB)
   │  Server  │                          │
   │  (SPOF)  │                ┌─────────┼─────────┐
   └──────────┘                │         │         │
                               ▼         ▼         ▼
                           Server 1  Server 2  Server 3
                           (nginx)   (nginx)   (nginx)
                               │         │         │
                               └────┬────┘         │
                                    │               │
                               App replicas   (auto-scaled)
                                    │
                            ┌───────┴────────┐
                            │                │
                    Primary DB          Replica DB(s)
                    (read/write)        (read-only)
                            │
                      Backup storage
                      (S3 / offsite)
```

### Docker Swarm HA Setup

```bash
# 3-manager Swarm for HA (odd number for Raft quorum)
# Manager 1 (init):
docker swarm init --advertise-addr <MANAGER-1-IP>

# Manager 2 & 3 (join as managers):
docker swarm join \
  --token $(docker swarm join-token -q manager) \
  <MANAGER-1-IP>:2377

# Workers:
docker swarm join \
  --token $(docker swarm join-token -q worker) \
  <MANAGER-1-IP>:2377

# Verify quorum:
docker node ls
# All managers should show "Active" and one "Leader"

# Drain a node for maintenance:
docker node update --availability drain <node-id>
# ... perform maintenance ...
docker node update --availability active <node-id>
```

---

## Zero Downtime Deployments

### Strategy 1: Rolling Update (Docker Swarm)

```bash
# 1. Build and push new image
docker build -t myrepo/myapp:v2.1.3 .
docker push myrepo/myapp:v2.1.3

# 2. Update service (rolling, zero downtime)
docker service update \
  --image myrepo/myapp:v2.1.3 \
  --update-parallelism 1 \
  --update-delay 30s \
  --update-monitor 60s \
  --update-failure-action rollback \
  --update-order start-first \      # NEW replicas start BEFORE old stop
  myapp_app

# 3. Monitor
watch docker service ps myapp_app

# 4. If bad: rollback
docker service rollback myapp_app
```

### Strategy 2: Blue-Green (Compose)

```bash
#!/bin/bash
# blue-green-deploy.sh

NEW_VERSION=$1
CURRENT=$(docker inspect myapp-nginx --format '{{index .Config.Labels "active"}}' 2>/dev/null || echo "blue")
NEW=$([ "$CURRENT" = "blue" ] && echo "green" || echo "blue")

echo "Deploying version $NEW_VERSION as $NEW (replacing $CURRENT)"

# 1. Start new version
docker compose \
  -p myapp-$NEW \
  -f docker-compose.yml \
  -f docker-compose.$NEW.yml \
  up -d --build

# 2. Wait for health checks
echo "Waiting for new version to be healthy..."
sleep 30

# 3. Run smoke tests
if ! curl -f http://localhost:8081/health; then
  echo "Health check failed! Rolling back..."
  docker compose -p myapp-$NEW down
  exit 1
fi

# 4. Switch nginx to new version
docker exec myapp-nginx nginx -s reload

# 5. Remove old version
echo "Deployment successful! Removing old version..."
docker compose -p myapp-$CURRENT down

echo "Done! $NEW is now live."
```

---

## Backup Strategy

```
BACKUP FREQUENCY:
─────────────────────────────────────────────────────────────────────

  Data type            Frequency    Retention    Location
  ───────────────────  ──────────   ─────────    ────────────────────
  Database (full)      Daily        30 days      S3 + offsite
  Database (WAL/binlog)Continuous   7 days       S3
  User uploads         Daily        90 days      S3
  Config files         On change    90 days      Git + encrypted S3
  Container volumes    Daily        14 days      S3
  Docker images        On push      10 versions  Registry
```

### Automated Database Backup

```yaml
# docker-compose.prod.yml (backup service)
services:
  db-backup:
    image: postgres:16-alpine
    environment:
      PGPASSWORD: ${POSTGRES_PASSWORD}
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      S3_BUCKET: ${BACKUP_S3_BUCKET}
    entrypoint: >
      /bin/sh -c "
        apk add --no-cache aws-cli;
        while true; do
          TIMESTAMP=$$(date +%Y%m%d_%H%M%S);
          echo 'Starting backup...';
          pg_dump -h db -U $$POSTGRES_USER $$POSTGRES_DB
            | gzip
            | aws s3 cp - s3://$$S3_BUCKET/db/backup_$$TIMESTAMP.sql.gz;
          aws s3 ls s3://$$S3_BUCKET/db/ --recursive
            | awk 'NR>30{print $$4}'
            | xargs -I{} aws s3 rm s3://$$S3_BUCKET/{};
          echo 'Backup complete: backup_'$$TIMESTAMP'.sql.gz';
          sleep 86400;
        done"
    networks:
      - backend
    restart: unless-stopped
    profiles: [backup]
```

### Backup Verification (Weekly)

```bash
#!/bin/bash
# verify-backup.sh — Test restoring from latest backup

BACKUP_FILE=$(aws s3 ls s3://mybucket/db/ | sort | tail -1 | awk '{print $4}')

echo "Testing backup: $BACKUP_FILE"

# Restore to test container
docker run --rm \
  -e POSTGRES_PASSWORD=testpass \
  -e POSTGRES_DB=testdb \
  --name restore-test \
  -d postgres:16

sleep 10

aws s3 cp s3://mybucket/db/$BACKUP_FILE - \
  | gunzip \
  | docker exec -i restore-test psql -U postgres testdb

# Run verification queries
docker exec restore-test psql -U postgres testdb -c "SELECT COUNT(*) FROM users;"

# Cleanup
docker rm -f restore-test

echo "Backup verification: SUCCESS"
```

---

## Incident Response

### Runbook: Container Down

```bash
# 1. Check what's happening
docker ps -a                           # Is it running?
docker logs --tail 100 <container>     # What does it say?
docker inspect <container>             # Full details

# 2. Check health
docker inspect --format='{{.State.Health}}' <container>

# 3. Check resources
docker stats --no-stream               # CPU/Memory/Network/IO

# 4. Check recent events
docker events --since 1h               # Recent Docker events

# 5. Check disk
docker system df                       # Docker disk usage
df -h                                  # Host disk usage

# 6. Immediate recovery
docker restart <container>             # Try restart
# OR if compose:
docker compose restart <service>
# OR force recreate:
docker compose up -d --force-recreate <service>

# 7. If all else fails
docker compose down && docker compose up -d   # Full restart
```

### Runbook: Out of Disk Space

```bash
# Diagnose
docker system df -v                    # Find what's using space
du -sh /var/lib/docker/*               # Docker data breakdown

# Clean up (SAFE — doesn't affect running containers)
docker system prune                    # Stopped containers + dangling images

# More aggressive (unused images too)
docker system prune -a

# ⚠️ DANGEROUS — removes volumes!
docker system prune -a --volumes

# Find large log files
find /var/lib/docker/containers -name '*.log' -size +100M

# Clear logs (without restarting)
truncate -s 0 /var/lib/docker/containers/<id>/<id>-json.log

# Prevent in future:
# Configure log rotation in daemon.json or compose logging config
```

---

## Performance Tuning

### Docker Daemon Settings

```json
// /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "default-ulimits": {
    "nofile": {
      "name": "nofile",
      "hard": 65536,
      "soft": 65536
    }
  },
  "metrics-addr": "0.0.0.0:9323",
  "experimental": true,
  "live-restore": true,
  "userland-proxy": false,
  "features": {
    "buildkit": true
  }
}
```

### System Tuning (Host)

```bash
# ── Network tuning for high-traffic services ──────────────────────────────────
cat >> /etc/sysctl.conf << EOF
# Increase connection limits
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# Reduce TIME_WAIT
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_tw_reuse = 1

# Increase file descriptor limits
fs.file-max = 2097152
EOF

sysctl -p

# ── System limits ─────────────────────────────────────────────────────────────
cat >> /etc/security/limits.conf << EOF
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
EOF
```

---

**🎉 Congratulations! You've completed the Docker learning path.**

Continue your journey:
- **[Kubernetes](https://kubernetes.io/docs/)** — Container orchestration at scale
- **[Terraform](https://terraform.io)** — Infrastructure as Code
- **[Helm](https://helm.sh)** — Kubernetes package manager
- **[Istio](https://istio.io)** — Service mesh for microservices
