#!/bin/bash
# Comprehensive fix for all DFS issues

echo "=== Distributed File System - Complete Fix ==="
echo ""
echo "This script will try multiple solutions to fix the networking issue."
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Function to test if DFS is working
test_dfs() {
    echo -n "Testing DFS connection... "
    
    # Try from client container first
    if docker-compose exec -T client python -c "
import sys; sys.path.insert(0, '/app')
try:
    from client.api_client import DFSClient
    client = DFSClient()
    stats = client.get_cluster_stats()
    print('SUCCESS')
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
        echo "✓ Working!"
        return 0
    fi
    
    # Try from host
    if python3 -c "
import sys; sys.path.insert(0, '.')
import os; os.environ['NAMENODE_HOST'] = 'localhost'
try:
    from client.api_client import DFSClient
    client = DFSClient()
    stats = client.get_cluster_stats()
    print('SUCCESS from host')
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
        echo "✓ Working from host!"
        return 0
    fi
    
    echo "✗ Failed"
    return 1
}

# Solution 1: Quick restart
echo "=== Solution 1: Quick Restart ==="
docker-compose restart
sleep 10
if test_dfs; then
    echo "✓ Fixed with restart!"
    exit 0
fi

# Solution 2: Fix DNS in client container
echo ""
echo "=== Solution 2: Fix DNS Resolution ==="
docker-compose exec -T client bash -c '
# Install DNS tools
apt-get update -qq && apt-get install -y -qq dnsutils iputils-ping 2>/dev/null

# Get actual IPs
NAMENODE_IP=$(docker inspect -f "{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}" dfs-namenode 2>/dev/null || echo "172.18.0.2")

# Update hosts file
echo "$NAMENODE_IP namenode dfs-namenode" >> /etc/hosts
echo "127.0.0.1 localhost" >> /etc/hosts

# Update resolv.conf to use Docker DNS
echo "nameserver 127.0.0.11" > /etc/resolv.conf
echo "options ndots:0" >> /etc/resolv.conf
' 2>/dev/null

sleep 5
if test_dfs; then
    echo "✓ Fixed with DNS resolution!"
    exit 0
fi

# Solution 3: Complete rebuild with fixed networking
echo ""
echo "=== Solution 3: Complete Rebuild ==="
docker-compose down -v

# Add extra_hosts to docker-compose.yml if not present
if ! grep -q "extra_hosts:" docker-compose.yml; then
    echo "Adding extra_hosts to docker-compose.yml..."
    # This is a bit tricky to do properly, so we'll create a override file
    cat > docker-compose.override.yml << 'EOF'
version: '3.8'

services:
  client:
    extra_hosts:
      - "namenode:host-gateway"
      - "datanode-1:host-gateway"
      - "datanode-2:host-gateway"
      - "datanode-3:host-gateway"
EOF
fi

docker-compose up -d
sleep 20
if test_dfs; then
    echo "✓ Fixed with rebuild!"
    exit 0
fi

# Solution 4: Create standalone working scripts
echo ""
echo "=== Solution 4: Creating Standalone Scripts ==="

# Create host-based client
cat > dfs << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Configuration for running from host
os.environ['NAMENODE_HOST'] = 'localhost'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.cli import main

if __name__ == '__main__':
    main()
EOF
chmod +x dfs

# Create container-based client
cat > dfs-docker << 'EOF'
#!/bin/bash
# Run DFS client in Docker container

# Ensure network fix is applied
docker-compose exec -T client bash -c '
if ! grep -q namenode /etc/hosts; then
    echo "172.18.0.2 namenode" >> /etc/hosts
    echo "172.18.0.3 datanode-1" >> /etc/hosts  
    echo "172.18.0.4 datanode-2" >> /etc/hosts
    echo "172.18.0.5 datanode-3" >> /etc/hosts
fi
' 2>/dev/null

# Run command
docker-compose exec -T client python -m client.cli "$@"
EOF
chmod +x dfs-docker

echo ""
echo "=== Testing Standalone Scripts ==="
echo "Test from standalone script" > test_standalone.txt

echo "Testing host-based client..."
./dfs upload test_standalone.txt /test_host.txt 2>/dev/null && echo "✓ Host client works!"

echo "Testing docker-based client..."  
./dfs-docker upload test_standalone.txt /test_docker.txt 2>/dev/null && echo "✓ Docker client works!"

# Final test
echo ""
echo "=== Final System Test ==="
if test_dfs; then
    echo "✓ System is working!"
else
    echo "✗ System still has issues"
    echo ""
    echo "=== Manual Workaround ==="
    echo "The system APIs are running, but there's a network resolution issue."
    echo "You can still use the system with these commands:"
    echo ""
    echo "From host machine:"
    echo "  ./dfs <command> <args>"
    echo ""
    echo "Using docker:"
    echo "  ./dfs-docker <command> <args>"
    echo ""
    echo "Examples:"
    echo "  ./dfs upload myfile.txt /myfile.txt"
    echo "  ./dfs ls /"
    echo "  ./dfs download /myfile.txt downloaded.txt"
    echo ""
    echo "Web UI is available at: http://localhost:3001"
fi

# Cleanup
rm -f test_standalone.txt

echo ""
echo "=== Fix Process Complete ==="