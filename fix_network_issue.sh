#!/bin/bash
# Fix network resolution issues

echo "=== Fixing Network Resolution Issues ==="
echo ""

# Step 1: Check if containers are on the same network
echo "Step 1: Checking Docker network..."
docker network inspect distributed-file-system_dfs-network | grep -A5 "Containers" || echo "Network not found"

# Step 2: Restart containers in correct order
echo ""
echo "Step 2: Restarting containers in correct order..."
docker-compose stop
docker-compose up -d namenode
sleep 5
docker-compose up -d datanode1 datanode2 datanode3
sleep 5
docker-compose up -d client prometheus grafana ui
sleep 10

# Step 3: Test network connectivity from client
echo ""
echo "Step 3: Testing network connectivity..."
echo "Installing network tools in client container..."
docker-compose exec -T client bash -c "apt-get update -qq && apt-get install -y -qq iputils-ping dnsutils netcat > /dev/null 2>&1 || true"

echo ""
echo "Testing DNS resolution:"
docker-compose exec -T client nslookup namenode || echo "DNS lookup failed"

echo ""
echo "Testing network connectivity:"
docker-compose exec -T client ping -c 2 namenode || echo "Ping failed"

echo ""
echo "Testing port connectivity:"
docker-compose exec -T client nc -zv namenode 8080 || echo "Port check failed"

# Step 4: Alternative fix - use IP addresses
echo ""
echo "Step 4: Getting container IPs..."
NAMENODE_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' dfs-namenode)
echo "NameNode IP: $NAMENODE_IP"

# Step 5: Create a fixed client script that uses IPs if hostnames fail
echo ""
echo "Step 5: Creating fallback client configuration..."
docker-compose exec -T client bash -c "cat > /app/client/network_fix.py << 'EOF'
import socket
import os

def get_namenode_host():
    # Try hostname first
    try:
        socket.gethostbyname('namenode')
        return 'namenode'
    except:
        # Fallback to container name
        try:
            socket.gethostbyname('dfs-namenode')
            return 'dfs-namenode'
        except:
            # Fallback to localhost if running from host
            return 'localhost'

# Export for use in client
NAMENODE_HOST = get_namenode_host()
print(f'Using NameNode host: {NAMENODE_HOST}')
EOF"

# Step 6: Test with direct connection
echo ""
echo "Step 6: Testing direct connection to NameNode..."
docker-compose exec -T client python -c "
import requests
try:
    # Try different hostnames
    hosts = ['namenode', 'dfs-namenode', 'localhost', '$NAMENODE_IP']
    for host in hosts:
        try:
            resp = requests.get(f'http://{host}:8080/health', timeout=2)
            if resp.status_code == 200:
                print(f'✓ Successfully connected to NameNode at {host}')
                break
        except:
            print(f'✗ Failed to connect to {host}')
            continue
except Exception as e:
    print(f'Error: {e}')
"

# Step 7: Apply workaround to common/constants.py
echo ""
echo "Step 7: Applying network workaround..."
docker-compose exec -T client bash -c "
# Backup original
cp /app/common/constants.py /app/common/constants.py.backup

# Check current NAMENODE_HOST setting
echo 'Current NAMENODE_HOST:'
grep NAMENODE_HOST /app/common/constants.py

# Update to use localhost when running from host
sed -i \"s/NAMENODE_HOST = 'namenode'/NAMENODE_HOST = os.environ.get('NAMENODE_HOST', 'namenode')/g\" /app/common/constants.py

# Add import if not present
grep -q 'import os' /app/common/constants.py || sed -i '1i import os' /app/common/constants.py
"

echo ""
echo "=== Network Fix Applied ==="
echo ""
echo "Now testing file operations..."

# Test upload with environment variable
docker-compose exec -T client bash -c "echo 'Network test successful!' > /workspace/network_test.txt"
docker-compose exec -T -e NAMENODE_HOST=namenode client python -m client.cli upload /workspace/network_test.txt /network_test.txt || \
docker-compose exec -T -e NAMENODE_HOST=dfs-namenode client python -m client.cli upload /workspace/network_test.txt /network_test.txt || \
docker-compose exec -T -e NAMENODE_HOST=localhost client python -m client.cli upload /workspace/network_test.txt /network_test.txt

echo ""
echo "Checking uploaded file..."
docker-compose exec -T -e NAMENODE_HOST=namenode client python -m client.cli ls / || \
docker-compose exec -T -e NAMENODE_HOST=dfs-namenode client python -m client.cli ls / || \
docker-compose exec -T -e NAMENODE_HOST=localhost client python -m client.cli ls /

echo ""
echo "If the upload still fails, try:"
echo "1. docker-compose down && docker-compose up -d"
echo "2. Run from host: python3 -m pip install -r requirements.txt"
echo "3. Run from host: NAMENODE_HOST=localhost python3 client/cli.py upload <file> <path>"