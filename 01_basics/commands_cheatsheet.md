# 🐳 Docker CLI — Complete Cheatsheet

> **Level:** 🟢 Beginner | **Reference:** Quick lookup for all essential commands

---

## 🏃 Running Containers

```bash
# ─── Basic Run ──────────────────────────────────────────────────────────────
docker run <image>                    # Run image (foreground)
docker run -d <image>                 # Run detached (background)
docker run -it <image> bash           # Interactive terminal
docker run --rm <image>               # Remove container after exit
docker run --name myapp <image>       # Named container

# ─── Port Mapping ───────────────────────────────────────────────────────────
docker run -p 8080:80 nginx           # host_port:container_port
docker run -p 127.0.0.1:8080:80 nginx # Bind to specific host IP
docker run -P nginx                   # Map ALL exposed ports randomly

# ─── Environment Variables ──────────────────────────────────────────────────
docker run -e DB_HOST=localhost nginx  # Single variable
docker run --env-file .env nginx       # From file

# ─── Resource Limits ────────────────────────────────────────────────────────
docker run --memory=512m nginx         # Memory limit
docker run --cpus=1.5 nginx            # CPU limit
docker run --memory=512m --cpus=1.5 nginx  # Both

# ─── Full Example ───────────────────────────────────────────────────────────
docker run -d \
  --name web-server \
  -p 8080:80 \
  -e NODE_ENV=production \
  --memory=256m \
  --restart unless-stopped \
  nginx:alpine
```

---

## 📋 Container Management

```bash
# ─── List ───────────────────────────────────────────────────────────────────
docker ps                             # Running containers
docker ps -a                          # All containers (including stopped)
docker ps -q                          # Only container IDs
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# ─── Start / Stop / Restart ─────────────────────────────────────────────────
docker start <container>              # Start stopped container
docker stop <container>               # Graceful stop (SIGTERM + 10s)
docker stop -t 30 <container>         # Custom timeout
docker kill <container>               # Force kill (SIGKILL)
docker restart <container>            # Stop + Start
docker pause <container>              # Freeze process
docker unpause <container>            # Unfreeze

# ─── Remove ─────────────────────────────────────────────────────────────────
docker rm <container>                 # Remove stopped container
docker rm -f <container>              # Force remove (even running)
docker rm $(docker ps -aq)            # Remove ALL stopped containers
docker container prune                # Remove all stopped containers

# ─── Inspect & Debug ────────────────────────────────────────────────────────
docker logs <container>               # View logs
docker logs -f <container>            # Follow logs (tail -f)
docker logs --tail 100 <container>    # Last 100 lines
docker logs --since 1h <container>    # Last hour
docker exec -it <container> bash      # Shell into running container
docker exec <container> ls /app       # Run command in container
docker inspect <container>            # Full JSON details
docker stats                          # Live resource usage
docker stats --no-stream              # One-time snapshot
docker top <container>                # Processes in container
docker diff <container>               # Filesystem changes
docker port <container>               # Port mappings
docker cp <container>:/path ./local   # Copy file from container
docker cp ./local <container>:/path   # Copy file to container
```

---

## 🖼️ Image Management

```bash
# ─── Pull / Push ────────────────────────────────────────────────────────────
docker pull nginx                     # Latest tag
docker pull nginx:1.25-alpine         # Specific version
docker pull ubuntu:22.04              # Specific OS version
docker push myrepo/myimage:v1.0       # Push to registry

# ─── List / Remove ──────────────────────────────────────────────────────────
docker images                         # List all images
docker images -a                      # Including intermediate layers
docker images --filter dangling=true  # Dangling (untagged) images
docker rmi <image>                    # Remove image
docker rmi $(docker images -q)        # Remove ALL images
docker image prune                    # Remove dangling images
docker image prune -a                 # Remove ALL unused images

# ─── Build ──────────────────────────────────────────────────────────────────
docker build .                        # Build from current dir
docker build -t myapp:v1.0 .          # With tag
docker build -t myapp:v1.0 -f Dockerfile.prod .  # Custom Dockerfile
docker build --no-cache .             # Skip cache
docker build --build-arg NODE_ENV=prod .  # Build argument

# ─── Inspect ────────────────────────────────────────────────────────────────
docker inspect <image>                # Full metadata
docker history <image>                # Layer history & sizes
docker image ls --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# ─── Save / Load (offline transfer) ─────────────────────────────────────────
docker save myimage:v1 | gzip > myimage.tar.gz    # Export to file
docker load < myimage.tar.gz                       # Import from file

# ─── Tag ────────────────────────────────────────────────────────────────────
docker tag myapp:latest myrepo/myapp:v1.0          # Create tag
docker tag myapp:v1.0 myapp:latest                 # Promote to latest
```

---

## 💾 Volume Management

```bash
# ─── Create / List / Remove ─────────────────────────────────────────────────
docker volume create mydata                       # Named volume
docker volume ls                                  # List volumes
docker volume inspect mydata                      # Inspect volume
docker volume rm mydata                           # Remove volume
docker volume prune                               # Remove unused volumes

# ─── Use in Containers ──────────────────────────────────────────────────────
docker run -v mydata:/app/data nginx              # Named volume
docker run -v /host/path:/container/path nginx    # Bind mount
docker run -v /host/path:/container/path:ro nginx # Read-only bind mount
docker run --mount type=volume,src=mydata,dst=/data nginx  # Mount syntax

# ─── Tmpfs (in-memory, not persisted) ───────────────────────────────────────
docker run --tmpfs /tmp nginx                     # Temporary filesystem
```

---

## 🌐 Network Management

```bash
# ─── Create / List / Remove ─────────────────────────────────────────────────
docker network create mynet                       # Bridge network (default)
docker network create --driver bridge mynet       # Explicit bridge
docker network create --driver overlay mynet      # Swarm overlay
docker network ls                                 # List networks
docker network inspect mynet                      # Inspect network
docker network rm mynet                           # Remove network
docker network prune                              # Remove unused networks

# ─── Connect Containers ─────────────────────────────────────────────────────
docker run --network mynet nginx                  # Join at start
docker network connect mynet <container>          # Join running container
docker network disconnect mynet <container>       # Disconnect container

# ─── Built-in Networks ──────────────────────────────────────────────────────
#  bridge   → Default, isolated, containers communicate by IP
#  host     → Share host network (no isolation)
#  none     → No network access (complete isolation)
```

---

## 🧹 Cleanup Commands

```bash
# ─── Targeted Cleanup ───────────────────────────────────────────────────────
docker container prune         # Remove stopped containers
docker image prune             # Remove dangling images
docker image prune -a          # Remove all unused images
docker volume prune            # Remove unused volumes
docker network prune           # Remove unused networks

# ─── Nuclear Option: Remove Everything ──────────────────────────────────────
docker system prune            # Containers + images + networks (stopped)
docker system prune -a         # + all unused images
docker system prune -a --volumes  # + volumes (⚠️ DATA LOSS!)

# ─── Check Disk Usage ───────────────────────────────────────────────────────
docker system df               # Overview of disk usage
docker system df -v            # Verbose breakdown
```

---

## 🏗️ Docker Compose Commands

```bash
# ─── Core Lifecycle ─────────────────────────────────────────────────────────
docker compose up              # Start services (foreground)
docker compose up -d           # Start services (background)
docker compose up --build      # Rebuild images before starting
docker compose down            # Stop and remove containers
docker compose down -v         # Also remove volumes
docker compose down --rmi all  # Also remove images

# ─── Control ────────────────────────────────────────────────────────────────
docker compose start           # Start existing containers
docker compose stop            # Stop without removing
docker compose restart         # Restart services
docker compose pause           # Pause all services
docker compose unpause         # Unpause

# ─── Scaling ────────────────────────────────────────────────────────────────
docker compose up --scale web=3  # Scale web service to 3 replicas

# ─── Logs & Debug ───────────────────────────────────────────────────────────
docker compose logs            # All service logs
docker compose logs -f web     # Follow specific service logs
docker compose ps              # Status of services
docker compose exec web bash   # Shell into service
docker compose run web npm test # One-off command

# ─── Multi-file ─────────────────────────────────────────────────────────────
docker compose -f docker-compose.yml -f docker-compose.prod.yml up
```

---

## 🔍 Useful One-Liners

```bash
# Remove all stopped containers
docker rm $(docker ps -aq --filter status=exited)

# Remove all dangling images
docker rmi $(docker images -qf dangling=true)

# Get IP address of a container
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' <container>

# Get environment variables of a container
docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' <container>

# Follow logs from multiple containers
docker compose logs -f web db redis

# Save running container as new image
docker commit <container> myimage:snapshot

# Live stream resource usage for all containers
docker stats $(docker ps --format '{{.Names}}')

# Find which container is using a port
docker ps --filter publish=8080

# Run a quick test container and clean up
docker run --rm -it busybox sh
```

---

## 📊 Command Quick Reference

```
LIFECYCLE:   create → start → (pause/unpause) → stop → rm
IMAGES:      build / pull → tag → push → rmi
NETWORK:     create → connect → disconnect → rm
VOLUMES:     create → (use in containers) → rm
CLEANUP:     prune (containers/images/volumes/networks/system)
```

---

**Next:** [Dockerfile Guide →](../02_images/dockerfile_guide.md)
