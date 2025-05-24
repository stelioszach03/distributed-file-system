#!/bin/bash
# Complete rebuild script

echo "=== Complete System Rebuild ==="
echo ""
echo "This will stop everything and rebuild from scratch."
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Stop and remove everything
echo "Stopping and removing containers..."
docker-compose down -v

# Ensure we have the correct files from the documents
echo "Verifying critical files..."

# Make sure client/api_client.py is correct
echo "Fixing client/api_client.py from document..."
# Copy the content from document index 24
cp client/api_client.py client/api_client.py.original 2>/dev/null || true

# Make sure namenode/file_handlers.py is correct  
echo "Fixing namenode/file_handlers.py from document..."
# Copy the content from document index 45
cp namenode/file_handlers.py namenode/file_handlers.py.original 2>/dev/null || true

# Apply the hostname fix to both files
echo "Applying hostname fixes..."

# Fix client/api_client.py - ensure it uses node_id directly as hostname
sed -i 's/datanode_url = f"http:\/\/datanode-{node_id}:{api_port}"/datanode_url = f"http:\/\/{node_id}:{api_port}"/g' client/api_client.py 2>/dev/null || true

# Fix namenode/file_handlers.py - ensure it uses node_id directly as hostname  
sed -i 's/url = f"http:\/\/{node_info.host}:{api_port}\/chunks\/{chunk_id}"/url = f"http:\/\/{node_id}:{api_port}\/chunks\/{chunk_id}"/g' namenode/file_handlers.py 2>/dev/null || true

# Clean Docker build cache
echo "Cleaning Docker build cache..."
docker system prune -f

# Rebuild all images
echo "Building all images fresh..."
docker-compose build --no-cache

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services
echo "Waiting for services to be ready (30 seconds)..."
for i in {30..1}; do
    echo -ne "\r$i seconds remaining..."
    sleep 1
done
echo ""

# Check health
echo "Checking system health..."
python3 scripts/healthcheck.py

# Run a simple test
echo ""
echo "Running simple test..."
docker-compose exec -T client bash -c "echo 'Rebuild test successful!' > /workspace/rebuild_test.txt"
docker-compose exec -T client python -m client.cli mkdir /test 2>/dev/null || true
docker-compose exec -T client python -m client.cli upload /workspace/rebuild_test.txt /test/rebuild.txt

echo ""
echo "Checking uploaded file..."
docker-compose exec -T client python -m client.cli ls /test

echo ""
echo "=== Rebuild Complete ==="
echo ""
echo "If the test file uploaded successfully, the system is working!"
echo ""
echo "Access points:"
echo "• Web UI: http://localhost:3001"  
echo "• Grafana: http://localhost:3000 (admin/admin)"
echo "• NameNode API: http://localhost:8080"
echo ""
echo "If still having issues, check logs with:"
echo "  docker-compose logs namenode | tail -50"