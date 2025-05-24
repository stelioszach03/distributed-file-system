#!/bin/bash
# Initialize Distributed File System with sample data

set -e

echo "=== Initializing Distributed File System ==="

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check if services are healthy
echo "Checking service health..."
docker-compose exec -T client python -m client.cli stats || {
    echo "Services not ready yet, waiting..."
    sleep 10
}

# Create directory structure
echo "Creating directory structure..."
docker-compose exec -T client python -m client.cli mkdir /data
docker-compose exec -T client python -m client.cli mkdir /data/documents
docker-compose exec -T client python -m client.cli mkdir /data/images
docker-compose exec -T client python -m client.cli mkdir /data/videos
docker-compose exec -T client python -m client.cli mkdir /backups
docker-compose exec -T client python -m client.cli mkdir /temp

# Create sample files for testing
echo "Creating sample files..."

# Create test files in workspace
docker-compose exec -T client bash -c "echo 'Welcome to Distributed File System!' > /workspace/welcome.txt"
docker-compose exec -T client bash -c "echo 'This is a test document.' > /workspace/test.txt"
docker-compose exec -T client bash -c "dd if=/dev/urandom of=/workspace/random_1mb.dat bs=1M count=1 2>/dev/null"
docker-compose exec -T client bash -c "dd if=/dev/urandom of=/workspace/random_10mb.dat bs=1M count=10 2>/dev/null"

# Upload files to DFS
echo "Uploading files to DFS..."
docker-compose exec -T client python -m client.cli upload /workspace/welcome.txt /data/documents/welcome.txt
docker-compose exec -T client python -m client.cli upload /workspace/test.txt /data/documents/test.txt
docker-compose exec -T client python -m client.cli upload /workspace/random_1mb.dat /data/documents/random_1mb.dat
docker-compose exec -T client python -m client.cli upload /workspace/random_10mb.dat /data/documents/random_10mb.dat

# List uploaded files
echo ""
echo "Listing uploaded files:"
docker-compose exec -T client python -m client.cli ls /data/documents

# Show cluster statistics
echo ""
echo "Cluster Statistics:"
docker-compose exec -T client python -m client.cli stats

# Run health check
echo ""
echo "Running health check..."
python3 scripts/healthcheck.py

echo ""
echo "=== Initialization Complete ==="
echo ""
echo "Access points:"
echo "- Web UI: http://localhost:3001"
echo "- Grafana: http://localhost:3000 (admin/admin)"
echo "- NameNode API: http://localhost:8080"
echo ""
echo "To access the CLI:"
echo "  docker-compose exec client bash"
echo "  python -m client.cli --help"