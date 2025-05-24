#!/bin/bash
# Script to check if all required files exist

echo "=== Checking Required Files ==="

MISSING_FILES=0

# Check UI files
UI_FILES=(
    "ui/package.json"
    "ui/src/App.js"
    "ui/src/index.js"
    "ui/src/index.css"
    "ui/src/reportWebVitals.js"
    "ui/src/services/api.js"
    "ui/src/components/FileExplorer.js"
    "ui/src/components/ClusterDashboard.js"
    "ui/src/components/StorageHeatmap.js"
    "ui/src/components/UploadModal.js"
    "ui/public/index.html"
)

# Check Python files
PYTHON_FILES=(
    "namenode/server.py"
    "namenode/api.py"
    "namenode/metadata_manager.py"
    "namenode/chunk_manager.py"
    "namenode/heartbeat_monitor.py"
    "namenode/file_handlers.py"
    "datanode/server.py"
    "datanode/storage_manager.py"
    "datanode/replication_manager.py"
    "datanode/health_reporter.py"
    "client/cli.py"
    "client/api_client.py"
    "common/constants.py"
    "common/messages.py"
    "common/utils.py"
)

# Check config files
CONFIG_FILES=(
    "docker-compose.yml"
    "docker/namenode.Dockerfile"
    "docker/datanode.Dockerfile"
    "docker/client.Dockerfile"
    "docker/ui.Dockerfile"
    "requirements.txt"
    "setup.py"
    "nginx.conf"
)

echo ""
echo "Checking UI files..."
for file in "${UI_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    else
        echo "✓ Found: $file"
    fi
done

echo ""
echo "Checking Python files..."
for file in "${PYTHON_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    else
        echo "✓ Found: $file"
    fi
done

echo ""
echo "Checking config files..."
for file in "${CONFIG_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    else
        echo "✓ Found: $file"
    fi
done

echo ""
echo "=== Summary ==="
if [ $MISSING_FILES -eq 0 ]; then
    echo "✓ All required files are present!"
else
    echo "❌ Missing $MISSING_FILES files"
    echo ""
    echo "Please ensure all files from the documents are created in their correct locations."
fi

# Check if required directories exist
echo ""
echo "Checking directories..."
DIRS=(
    "ui/src/components"
    "ui/src/services"
    "ui/public"
    "namenode"
    "datanode"
    "client"
    "common"
    "docker"
    "scripts"
    "monitoring/prometheus"
    "monitoring/grafana/dashboards"
)

for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "Creating directory: $dir"
        mkdir -p "$dir"
    fi
done

echo ""
echo "Done!"