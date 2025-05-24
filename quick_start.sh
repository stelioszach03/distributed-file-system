#!/bin/bash
# Quick start script for the Distributed File System

echo "=== Quick Start for Distributed File System ==="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Give execute permissions
chmod +x fix_upload_issue.sh test_system.sh

# Apply the upload fix
echo "Applying upload fix..."
./fix_upload_issue.sh

# Wait a bit more
echo ""
echo "Waiting for system to stabilize..."
sleep 10

# Run system tests
echo ""
echo "Running system tests..."
./test_system.sh

# Show final status
echo ""
echo "=== Quick Start Complete ==="
echo ""
echo "System Status:"
docker-compose ps
echo ""
echo "You can now access:"
echo "• Web UI: http://localhost:3001"
echo "• Grafana Dashboard: http://localhost:3000 (username: admin, password: admin)"
echo "• NameNode API: http://localhost:8080"
echo ""
echo "Useful Commands:"
echo "• View logs: docker-compose logs -f"
echo "• Access CLI: docker-compose exec client bash"
echo "• Upload file: docker-compose exec client python -m client.cli upload <local> <remote>"
echo "• List files: docker-compose exec client python -m client.cli ls /"
echo "• Stop system: docker-compose down"
echo "• Stop and remove data: docker-compose down -v"