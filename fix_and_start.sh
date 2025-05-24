#!/bin/bash
# Complete fix and start script

echo "=== Fixing and Starting Distributed File System ==="

# Step 1: Clean everything
echo "Cleaning old containers and networks..."
docker-compose down
docker network rm distributed-file-system_dfs-network 2>/dev/null || true

# Step 2: Remove docker-compose.override.yml if it exists (causes issues)
if [ -f "docker-compose.override.yml" ]; then
    echo "Removing docker-compose.override.yml..."
    rm docker-compose.override.yml
fi

# Step 3: Build images first
echo ""
echo "Building Docker images..."
docker-compose build

# Step 4: Start services
echo ""
echo "Starting services..."
docker-compose up -d

# Step 5: Wait and check
echo ""
echo "Waiting for services to start (30 seconds)..."
for i in {30..1}; do
    echo -ne "\r$i seconds remaining..."
    sleep 1
done
echo ""

# Step 6: Check what's running
echo ""
echo "Checking services..."
docker-compose ps

# Step 7: Check logs for errors
echo ""
echo "Checking for errors..."
docker-compose logs --tail=10 | grep -i error || echo "No obvious errors found"

# Step 8: Test connections
echo ""
echo "Testing connections..."
echo -n "NameNode API: "
curl -s http://localhost:8080/health 2>/dev/null && echo " ✓" || echo " ✗"

echo -n "Web UI: "
curl -s http://localhost:3001 >/dev/null 2>&1 && echo " ✓" || echo " ✗"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "If services are not running, check logs with:"
echo "  docker-compose logs <service-name>"
echo ""
echo "Services: namenode, datanode1, datanode2, datanode3, client, ui, prometheus, grafana"