# 🐳 Module 04 — Docker Networking Deep Dive

> **Level:** 🟡 Intermediate | **Time:** ~2.5 hours | **Prerequisites:** Module 03

---

## 📖 Table of Contents

- [Network Drivers Overview](#network-drivers-overview)
- [Bridge Networks](#bridge-networks)
- [Host Networking](#host-networking)
- [Overlay Networks (Swarm)](#overlay-networks-swarm)
- [Container DNS](#container-dns)
- [Port Binding Internals](#port-binding-internals)
- [Network Security Patterns](#network-security-patterns)
- [Practical Examples](#practical-examples)

---

## Network Drivers Overview

```
DRIVER       USE CASE                    ISOLATION    PERFORMANCE
──────────   ─────────────────────────   ─────────    ───────────
bridge       Default, single host        Medium       Good
host         Max performance, no NAT     None         Best
overlay      Multi-host (Swarm/K8s)      High         Moderate
macvlan      Need real MAC/IP on LAN     High         Native
ipvlan       Similar to macvlan, L3      High         Native
none         Full isolation, no network  Complete     N/A
```

---

## Bridge Networks

### Default Bridge (docker0)

```
HOST MACHINE
┌──────────────────────────────────────────────────────────────┐
│  eth0 (172.16.0.1) ◄──── internet                           │
│                                                              │
│  docker0 (172.17.0.1) ◄──── NAT bridge                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Default Bridge Network                  │   │
│  │                172.17.0.0/16                         │   │
│  │                                                      │   │
│  │   Container A          Container B                   │   │
│  │   172.17.0.2           172.17.0.3                    │   │
│  │   ┌──────────┐         ┌──────────┐                  │   │
│  │   │  veth0   │         │  veth1   │                  │   │
│  │   └────┬─────┘         └────┬─────┘                  │   │
│  │        │                    │                         │   │
│  │  ──────┴────────────────────┴──────────────────────  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ⚠️  Default bridge: containers cannot resolve by NAME       │
│  ✅  Custom bridge: DNS resolution by container name works!  │
└──────────────────────────────────────────────────────────────┘
```

### Custom Bridge (Recommended)

```bash
# Create custom bridge network
docker network create \
  --driver bridge \
  --subnet 192.168.10.0/24 \
  --gateway 192.168.10.1 \
  --ip-range 192.168.10.128/25 \
  myapp_network

# Custom bridge benefits:
# ✅ Container DNS resolution (ping by name!)
# ✅ Better isolation
# ✅ Custom subnets
# ✅ connect/disconnect at runtime
```

---

## Host Networking

```
HOST NETWORK MODE
─────────────────

Without host mode:                With host mode:
┌─────────────────┐              ┌─────────────────┐
│  HOST :8080     │              │  HOST :80        │
│       │ NAT     │              │  (shared with    │
│  Container :80  │              │   container)     │
└─────────────────┘              └─────────────────┘

docker run --network host nginx
# nginx now listens on HOST port 80 directly
# No port mapping needed (-p ignored!)
# Maximum performance, no NAT overhead
```

```yaml
# In Compose:
services:
  nginx:
    image: nginx
    network_mode: host
    # ⚠️ Don't use 'ports:' with host mode!
```

**Use cases:**
- Performance-critical applications
- Network monitoring tools
- Services that need to bind to many dynamic ports

**Drawbacks:**
- No network isolation
- Port conflicts with host
- Only works on Linux (not Mac/Windows)

---

## Overlay Networks (Swarm)

```
MULTI-HOST OVERLAY NETWORK
──────────────────────────

Host 1 (manager)              Host 2 (worker)
┌──────────────────────┐     ┌──────────────────────┐
│  ┌────────────────┐  │     │  ┌────────────────┐  │
│  │  web replica 1 │  │     │  │  web replica 2 │  │
│  │  10.0.1.3      │  │     │  │  10.0.1.4      │  │
│  └───────┬────────┘  │     │  └───────┬────────┘  │
│          │ VXLAN     │     │          │ VXLAN     │
│  ┌───────▼────────┐  │     │  ┌───────▼────────┐  │
│  │  Overlay Net   │  │     │  │  Overlay Net   │  │
│  │  10.0.1.0/24   │◄─┼─────┼─▶│  10.0.1.0/24  │  │
│  └────────────────┘  │     │  └────────────────┘  │
│  eth0: 192.168.1.1   │     │  eth0: 192.168.1.2   │
└──────────────────────┘     └──────────────────────┘
         │                            │
         └───────── LAN ──────────────┘

VXLAN: Virtual Extensible LAN — tunnels L2 over L3/UDP port 4789
```

```bash
# Create overlay network (requires Swarm mode)
docker swarm init
docker network create --driver overlay --attachable myoverlay
```

---

## Container DNS

```
┌──────────────────────────────────────────────────────────────┐
│                    DOCKER EMBEDDED DNS                       │
│                                                              │
│  Container: "api"                                            │
│  ┌──────────────────────────────────────────────────┐       │
│  │  /etc/resolv.conf                                │       │
│  │  nameserver 127.0.0.11   ← Docker's DNS server   │       │
│  │  search myproject_default.                       │       │
│  └──────────────────────────────────────────────────┘       │
│                         │                                    │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────┐       │
│  │          Docker Embedded DNS (127.0.0.11)        │       │
│  │                                                  │       │
│  │  Query: "db" → 172.20.0.5 (db container IP)      │       │
│  │  Query: "redis" → 172.20.0.6                     │       │
│  │  Query: "google.com" → external resolver         │       │
│  └──────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────┘

# In custom bridge networks:
# ✅ ping db          → works (service name)
# ✅ ping my-db-1     → works (container name)
# ✅ ping db.mynet    → works (FQDN)
# ❌ ping 172.20.0.5  → works but not recommended (IP changes!)
```

### DNS Aliases

```yaml
services:
  db:
    image: postgres
    networks:
      backend:
        aliases:
          - database      # Another name for this service
          - postgres-main

  # Now both 'db' and 'database' resolve to the same container
```

---

## Port Binding Internals

```
docker run -p 8080:80 nginx

HOST                          CONTAINER
eth0:8080  ──iptables NAT──▶  veth:80
           (DOCKER-chain)

iptables rules added:
-A DOCKER -d 0.0.0.0/0 -p tcp --dport 8080 -j DNAT --to 172.17.0.2:80
-A POSTROUTING -s 172.17.0.2/32 -d 172.17.0.2/32 -p tcp --dport 80 -j MASQUERADE

# Check rules:
sudo iptables -t nat -L DOCKER --line-numbers

Port binding options:
  -p 80:80          → Bind on all interfaces (0.0.0.0:80)
  -p 127.0.0.1:80:80 → Bind only on localhost
  -p 80:80/udp      → UDP port
  -P                 → Random high ports for all EXPOSED ports
```

---

## Network Security Patterns

### 1. DMZ Pattern (Frontend / Backend Separation)

```yaml
services:
  nginx:       # Public-facing
    networks: [public, internal]

  api:         # Internal only
    networks: [internal, data]

  db:          # No public access
    networks: [data]

networks:
  public:      # Internet-accessible
    driver: bridge
  internal:    # App tier
    driver: bridge
  data:        # Data tier
    driver: bridge
    internal: true   # ← No external routing!
```

```
Internet → [public] → nginx → [internal] → api → [data] → db
                                                          ↑
                                              No internet access!
```

### 2. Network Policies (with labels)

```yaml
# Combine with firewall rules for production
services:
  db:
    networks:
      - data
    labels:
      com.example.network.policy: "restricted"
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /run
```

---

## Practical Examples

### Example: Service Discovery

```bash
# Start two containers on same network
docker network create testnet
docker run -d --name db --network testnet postgres:16
docker run -d --name app --network testnet myapp

# From 'app' container, reach 'db' by name:
docker exec app ping db                # Works!
docker exec app curl http://db:5432    # Works!
docker exec app nslookup db            # Returns db's IP
```

### Example: Inspect Network

```bash
docker network inspect testnet

# Shows:
# - Subnet, gateway
# - Connected containers with their IPs
# - Options and labels

# Pretty format:
docker network inspect testnet \
  --format '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}'
```

### Example: Connect to Multiple Networks

```bash
# Container can join multiple networks!
docker run -d --name proxy --network frontend nginx
docker network connect backend proxy

# Now 'proxy' can reach both frontend and backend containers
docker inspect proxy --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}: {{$v.IPAddress}}{{"\n"}}{{end}}'
```

---

## Network Troubleshooting

```bash
# Check container network config
docker inspect <container> | jq '.[0].NetworkSettings'

# Test connectivity between containers
docker exec app ping -c 3 db
docker exec app curl -v http://db:5432

# View iptables rules
sudo iptables -t nat -L DOCKER -n -v

# Check which containers are on a network
docker network inspect mynet --format \
  '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'

# Diagnose DNS
docker exec app nslookup db
docker exec app cat /etc/resolv.conf

# Network bandwidth test
docker run --rm --network mynet \
  networkstatic/iperf3 iperf3 -s &
docker run --rm --network mynet \
  networkstatic/iperf3 iperf3 -c <server-ip>
```

---

**Next:** [Storage & Volumes Guide →](../05_storage/volumes_guide.md)
