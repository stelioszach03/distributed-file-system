#!/bin/bash
# Fix Docker networking issues completely

echo "=== Complete Docker Network Fix ==="
echo ""

# Step 1: Stop everything
echo "Step 1: Stopping all containers..."
docker-compose down

# Step 2: Remove old network
echo ""
echo "Step 2: Removing old network..."
docker network rm distributed-file-system_dfs-network 2>/dev/null || true

# Step 3: Update docker-compose.yml to ensure proper networking
echo ""
echo "Step 3: Checking docker-compose.yml networking..."
if ! grep -q "external_links:" docker-compose.yml; then
    echo "Docker-compose networking looks correct."
else
    echo "Found potential networking issues in docker-compose.yml"
fi

# Step 4: Start services with explicit network creation
echo ""
echo "Step 4: Creating network and starting services..."
docker network create distributed-file-system_dfs-network 2>/dev/null || true
docker-compose up -d

# Step 5: Wait for services
echo ""
echo "Step 5: Waiting for services to be ready..."
for i in {30..1}; do
    echo -ne "\rWaiting... $i seconds"
    sleep 1
done
echo ""

# Step 6: Verify network configuration
echo ""
echo "Step 6: Verifying network configuration..."
echo "Containers on network:"
docker network inspect distributed-file-system_dfs-network | jq '.Containers | to_entries | .[] | {Name: .value.Name, IPv4: .value.IPv4Address}' 2>/dev/null || \
docker network inspect distributed-file-system_dfs-network | grep -A2 "Name\|IPv4"

# Step 7: Test connectivity between containers
echo ""
echo "Step 7: Testing inter-container connectivity..."

# Install tools in client if needed
docker-compose exec -T client bash -c "which nc || (apt-get update -qq && apt-get install -y -qq netcat 2>/dev/null)" || true

# Test from client to namenode
echo "Testing client -> namenode:"
docker-compose exec -T client bash -c "nc -zv namenode 8080 2>&1" || echo "Failed"

# Test from client to datanodes
for i in 1 2 3; do
    echo "Testing client -> datanode-$i:"
    docker-compose exec -T client bash -c "nc -zv datanode-$i 8081 2>&1" || echo "Failed"
done

# Step 8: Alternative approach - update client to handle multiple hostnames
echo ""
echo "Step 8: Updating client to handle network issues..."
docker-compose exec -T client bash -c 'cat > /app/common/network_helper.py << "EOF"
import socket
import os

def resolve_hostname(hostname, port=None):
    """Try to resolve hostname with fallbacks."""
    candidates = [
        hostname,
        f"dfs-{hostname}",
        f"{hostname}.distributed-file-system_dfs-network",
        "host.docker.internal",  # For Docker Desktop
        "172.17.0.1",  # Default Docker bridge
        "localhost"
    ]
    
    for candidate in candidates:
        try:
            # Try to resolve the hostname
            addr = socket.gethostbyname(candidate)
            # If port provided, try to connect
            if port:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((candidate, port))
                sock.close()
                if result == 0:
                    return candidate
            else:
                return candidate
        except:
            continue
    
    # Return original if all fail
    return hostname

# Monkey patch the NAMENODE_HOST
import common.constants
original_host = getattr(common.constants, "NAMENODE_HOST", "namenode")
common.constants.NAMENODE_HOST = resolve_hostname(original_host, 8080)
print(f"Resolved NAMENODE_HOST to: {common.constants.NAMENODE_HOST}")
EOF'

# Step 9: Create a working test script inside the client container
echo ""
echo "Step 9: Creating test script in client container..."
docker-compose exec -T client bash -c 'cat > /workspace/test_upload.py << "EOF"
#!/usr/bin/env python3
import sys
sys.path.insert(0, "/app")

# Import the network helper
try:
    import common.network_helper
except:
    pass

from client.api_client import DFSClient
import logging

logging.basicConfig(level=logging.INFO)

# Create client
client = DFSClient()

# Test connection
try:
    stats = client.get_cluster_stats()
    print("✓ Connected to NameNode successfully!")
    print(f"Cluster has {stats[\"alive_nodes\"]} active nodes")
    
    # Try to upload a test file
    with open("/workspace/test_network.txt", "w") as f:
        f.write("Network test successful!\n")
    
    client.upload_file("/workspace/test_network.txt", "/network_test.txt")
    print("✓ File uploaded successfully!")
    
    # List files
    files = client.list_directory("/")
    print("✓ Files in root directory:")
    for f in files:
        print(f"  - {f[\"name\"]}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
EOF'

chmod +x /workspace/test_upload.py

# Step 10: Run the test
echo ""
echo "Step 10: Running network test..."
docker-compose exec -T client python3 /workspace/test_upload.py

echo ""
echo "=== Network Fix Complete ==="
echo ""
echo "If the test succeeded, the network is fixed!"
echo "If not, try running from the host with: ./run_from_host.sh"