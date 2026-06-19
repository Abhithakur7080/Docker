# 🐳 Module 11 — Monitoring & Observability

> **Level:** 🔴 Advanced | **Time:** ~3 hours | **Prerequisites:** Modules 01-10

---

## 📖 Table of Contents

- [Observability Pillars](#observability-pillars)
- [Monitoring Stack Overview](#monitoring-stack-overview)
- [Prometheus Metrics](#prometheus-metrics)
- [Grafana Dashboards](#grafana-dashboards)
- [Container Health Monitoring](#container-health-monitoring)
- [Log Aggregation](#log-aggregation)
- [Alerting](#alerting)
- [Key Metrics to Watch](#key-metrics-to-watch)

---

## Observability Pillars

```
┌──────────────────────────────────────────────────────────────────┐
│                  THE THREE PILLARS OF OBSERVABILITY              │
├──────────────────┬──────────────────┬────────────────────────────┤
│    📊 METRICS    │    📋 LOGS       │    🔍 TRACES               │
├──────────────────┼──────────────────┼────────────────────────────┤
│ Numeric data     │ Text events      │ Request flow across        │
│ over time        │ with timestamps  │ services                   │
│                  │                  │                            │
│ CPU usage        │ Error messages   │ user → api → db            │
│ Memory %         │ Request logs     │ Latency per hop            │
│ Request rate     │ Audit trail      │ Bottleneck finding         │
│ Error rate       │ Debug output     │                            │
│                  │                  │                            │
│ Tool: Prometheus │ Tool: ELK/Loki   │ Tool: Jaeger/Tempo/Zipkin  │
└──────────────────┴──────────────────┴────────────────────────────┘
```

---

## Monitoring Stack Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       MONITORING ARCHITECTURE                           │
│                                                                         │
│    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │
│    │  App A   │  │  App B   │  │ Database │  │   Host System    │     │
│    │/metrics  │  │/metrics  │  │          │  │                  │     │
│    └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────────┘     │
│         │             │             │                │                  │
│         │        postgres-exporter  │           node-exporter           │
│         │             │             │                │                  │
│    ─────┴─────────────┴─────────────┴────────────────┴──────────        │
│                               │ PULL                                    │
│                               ▼                                         │
│                     ┌──────────────────┐                                │
│                     │    Prometheus    │ ← Scrape every 15s             │
│                     │  (time series DB)│                                │
│                     └────────┬─────────┘                                │
│                              │                                          │
│               ┌──────────────┼──────────────┐                          │
│               ▼              ▼              ▼                           │
│    ┌──────────────┐ ┌─────────────┐ ┌──────────────┐                  │
│    │   Grafana    │ │ AlertManager│ │   Recording  │                  │
│    │  Dashboards  │ │ (PagerDuty/ │ │    Rules     │                  │
│    │              │ │   Slack)    │ │              │                  │
│    └──────────────┘ └─────────────┘ └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Prometheus Metrics

### Metric Types

```
┌──────────────────────────────────────────────────────────────────────┐
│                    PROMETHEUS METRIC TYPES                           │
├───────────────┬──────────────────────────────────────────────────────┤
│  Counter      │ Monotonically increasing value (resets on restart)   │
│               │ Example: http_requests_total                         │
│               │ Use for: requests, errors, bytes sent                │
├───────────────┼──────────────────────────────────────────────────────┤
│  Gauge        │ Can go up and down                                   │
│               │ Example: memory_usage_bytes, active_connections      │
│               │ Use for: current state measurements                  │
├───────────────┼──────────────────────────────────────────────────────┤
│  Histogram    │ Sample observations in buckets + sum + count         │
│               │ Example: http_request_duration_seconds               │
│               │ Use for: latency, request size, response size        │
├───────────────┼──────────────────────────────────────────────────────┤
│  Summary      │ Similar to histogram (calculates quantiles)          │
│               │ Example: rpc_duration_seconds{quantile="0.99"}       │
│               │ Use for: p50, p95, p99 latencies                    │
└───────────────┴──────────────────────────────────────────────────────┘
```

### Key PromQL Queries

```promql
# ── Container CPU Usage ───────────────────────────────────────────────────────
rate(container_cpu_usage_seconds_total{name!=""}[5m]) * 100

# ── Container Memory Usage ────────────────────────────────────────────────────
container_memory_usage_bytes{name!=""} / 1024 / 1024

# ── Container Memory Limit % ─────────────────────────────────────────────────
container_memory_usage_bytes{name!=""} / container_spec_memory_limit_bytes * 100

# ── HTTP Request Rate ─────────────────────────────────────────────────────────
rate(http_requests_total[5m])

# ── HTTP Error Rate ───────────────────────────────────────────────────────────
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100

# ── p99 Latency ───────────────────────────────────────────────────────────────
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# ── Node Disk Usage ───────────────────────────────────────────────────────────
(node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100

# ── Available Disk ────────────────────────────────────────────────────────────
node_filesystem_avail_bytes{mountpoint="/"} / 1024 / 1024 / 1024

# ── PostgreSQL Active Connections ─────────────────────────────────────────────
pg_stat_database_numbackends

# ── Redis Memory Usage ────────────────────────────────────────────────────────
redis_memory_used_bytes / redis_memory_max_bytes * 100
```

---

## Container Health Monitoring

### Docker Health Check Patterns

```bash
# Check container health status
docker inspect --format='{{.State.Health.Status}}' <container>

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' <container>

# Monitor health in real-time
watch -n 2 'docker ps --format "table {{.Names}}\t{{.Status}}"'

# Alert on unhealthy containers
docker events --filter 'event=health_status' --filter 'health_status=unhealthy'
```

### Automated Health Monitoring Script

```bash
#!/bin/bash
# monitor-containers.sh — Alert when containers are unhealthy

SLACK_WEBHOOK="${SLACK_WEBHOOK_URL}"

check_health() {
  while true; do
    UNHEALTHY=$(docker ps --filter health=unhealthy --format '{{.Names}}')
    EXITED=$(docker ps -a --filter status=exited --filter label=com.myapp.service --format '{{.Names}}')

    if [ -n "$UNHEALTHY" ]; then
      MSG="🚨 UNHEALTHY containers: $UNHEALTHY"
      curl -s -X POST "$SLACK_WEBHOOK" \
        -H 'Content-type: application/json' \
        --data "{\"text\":\"$MSG\"}"
    fi

    if [ -n "$EXITED" ]; then
      MSG="💀 EXITED containers: $EXITED"
      curl -s -X POST "$SLACK_WEBHOOK" \
        -H 'Content-type: application/json' \
        --data "{\"text\":\"$MSG\"}"
    fi

    sleep 60
  done
}

check_health
```

---

## Log Aggregation

### Loki + Promtail Stack

```yaml
# Add to monitoring docker-compose.yml

  loki:
    image: grafana/loki:2.9.4
    container_name: loki
    command: -config.file=/etc/loki/local-config.yaml
    ports:
      - "127.0.0.1:3100:3100"
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yaml:ro
      - loki_data:/loki
    networks:
      - monitoring

  promtail:
    image: grafana/promtail:2.9.4
    container_name: promtail
    command: -config.file=/etc/promtail/config.yml
    volumes:
      - ./promtail-config.yml:/etc/promtail/config.yml:ro
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - monitoring
    depends_on:
      - loki
```

```yaml
# promtail-config.yml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: 'container'
      - source_labels: ['__meta_docker_container_label_com_myapp_service']
        target_label: 'service'
    pipeline_stages:
      - json:
          expressions:
            level: level
            message: message
            timestamp: timestamp
      - labels:
          level:
      - timestamp:
          source: timestamp
          format: RFC3339
```

---

## Alerting

### Alert Rules (Prometheus)

```yaml
# rules/docker-alerts.yml
groups:
  - name: container-alerts
    rules:
      # Container is down
      - alert: ContainerDown
        expr: absent(container_last_seen{name!=""})
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Container {{ $labels.name }} is down"
          description: "Container has been absent for more than 1 minute"

      # High CPU usage
      - alert: ContainerHighCPU
        expr: rate(container_cpu_usage_seconds_total{name!=""}[5m]) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU in {{ $labels.name }}: {{ $value }}%"

      # Memory close to limit
      - alert: ContainerHighMemory
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes * 100 > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory in {{ $labels.name }}: {{ $value }}%"

      # Container restarting too often
      - alert: ContainerRestartLoop
        expr: rate(container_restart_count[10m]) > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Container {{ $labels.name }} is in a restart loop"

  - name: host-alerts
    rules:
      # Disk space > 80%
      - alert: DiskSpaceHigh
        expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk usage high: {{ $value }}%"

      # Disk space > 95% = critical
      - alert: DiskSpaceCritical
        expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100 > 95
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "CRITICAL: Disk almost full: {{ $value }}%"

      # High memory usage
      - alert: HostHighMemory
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 90
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Host memory usage: {{ $value }}%"
```

---

## Key Metrics to Watch

```
GOLDEN SIGNALS (per Google SRE)
────────────────────────────────────────────────────────────────────────

  1. LATENCY    How long requests take
               p50, p95, p99 response times
               Alert: p99 > 500ms

  2. TRAFFIC    How much demand your system handles
               Requests per second (RPS)
               Alert: unusual spikes or drops

  3. ERRORS     Rate of failed requests
               HTTP 5xx errors / total requests * 100
               Alert: error rate > 1%

  4. SATURATION How full your system is
               CPU %, Memory %, Disk I/O, Network I/O
               Alert: Memory > 90%, CPU > 80% sustained

DOCKER-SPECIFIC METRICS TO MONITOR
────────────────────────────────────────────────────────────────────────

  Container         Metric                         Alert
  ─────────────     ──────────────────────────     ────────────────────
  All               container_last_seen absent      Container down
  All               cpu_usage > 80%                High CPU
  All               memory / limit > 90%            Memory pressure
  All               restart_count increasing         Restart loop
  App               http_5xx / total > 1%           Error spike
  App               p99_latency > 500ms             Slow responses
  DB (Postgres)     connections > max * 80%          Connection pool
  DB (Postgres)     deadlocks increasing            DB issues
  Redis             memory / max > 90%              Cache pressure
  Redis             rejected_connections > 0        Cache full
  Host              disk > 80%                     Disk pressure
  Host              load > CPU_count * 2            Overloaded
```

---

**Next:** [Best Practices →](../12_best_practices/best_practices.md)
