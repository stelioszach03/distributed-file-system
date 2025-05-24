#!/bin/bash
# Setup script for the distributed file system cluster

set -e

echo "Setting up Distributed File System Cluster..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Build images
echo "Building Docker images..."
docker-compose build

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10

# Check service status
echo "Checking service status..."
docker-compose ps

# Show logs
echo "Recent logs:"
docker-compose logs --tail=20

echo "Cluster setup complete!"
echo ""
echo "Access points:"
echo "- NameNode API: http://localhost:8080"
echo "- Grafana Dashboard: http://localhost:3000 (admin/admin)"
echo "- Prometheus: http://localhost:9094"
echo ""
echo "To access the CLI, run:"
echo "  docker-compose exec client dfs-cli --help"
echo ""
echo "To stop the cluster, run:"
echo "  docker-compose down"