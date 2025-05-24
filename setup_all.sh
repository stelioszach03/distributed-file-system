#!/bin/bash
# Master setup script for Distributed File System

set -e

echo "=== Distributed File System Complete Setup ==="
echo ""

# Step 1: Check files
echo "Step 1: Checking file integrity..."
bash check_files.sh

# Step 2: Install dependencies
echo ""
echo "Step 2: Installing system dependencies..."
bash install_deps.sh

# Step 3: Fix and run
echo ""
echo "Step 3: Fixing issues and starting system..."
bash fix_and_run.sh

echo ""
echo "=== Setup Process Complete ==="
echo ""
echo "If everything worked correctly, you should be able to access:"
echo "- Web UI: http://localhost:3001"
echo "- Grafana: http://localhost:3000"
echo "- NameNode API: http://localhost:8080"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"