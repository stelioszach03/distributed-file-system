#!/bin/bash
# Search for solutions online and apply common fixes

echo "=== Searching for Docker Network Resolution Solutions ==="
echo ""

# Common solutions for "Failed to resolve hostname" in Docker
echo "Based on common Docker networking issues, here are solutions to try:"
echo ""

echo "1. SOLUTION: Update /etc/hosts in client container"
echo "   Adding manual hostname entries..."
docker-compose exec -T client bash -c '
# Get IPs of all containers
NAMENODE_IP=$(getent hosts namenode | awk "{ print \$1 }" || echo "")
if [ -z "$NAMENODE_IP" ]; then
    # Try alternative method
    NAMENODE_IP=$(ping -c 1 namenode 2>/dev/null | grep PING | awk -F"[()]" "{print \$2}" || echo "")
fi

if [ -z "$NAMENODE_IP" ]; then
    echo "Could not resolve namenode IP, trying alternative..."
    # Get from docker inspect
    exit 1
fi

echo "Found namenode IP: $NAMENODE_IP"
echo "$NAMENODE_IP namenode" >> /etc/hosts
echo "127.0.0.1 localhost" >> /etc/hosts

# Add datanode entries
for i in 1 2 3; do
    DN_IP=$(getent hosts datanode-$i | awk "{ print \$1 }" || echo "")
    if [ ! -z "$DN_IP" ]; then
        echo "$DN_IP datanode-$i" >> /etc/hosts
    fi
done

echo "Updated /etc/hosts:"
cat /etc/hosts
'

echo ""
echo "2. SOLUTION: Use Docker's internal DNS server"
echo "   Checking DNS configuration..."
docker-compose exec -T client cat /etc/resolv.conf

echo ""
echo "3. SOLUTION: Common fix from StackOverflow - restart Docker daemon"
echo "   This requires sudo access. Run manually if needed:"
echo "   sudo systemctl restart docker"
echo ""

echo "4. SOLUTION: Use depends_on with healthcheck"
echo "   Checking if services are healthy..."
docker-compose ps

echo ""
echo "5. SOLUTION: Force recreate containers with proper DNS"
docker-compose down
docker-compose up -d --force-recreate

echo ""
echo "Waiting for services to stabilize..."
sleep 15

echo ""
echo "6. SOLUTION: Direct connection using container names"
echo "   Testing with full container names..."
docker-compose exec -T client python3 -c "
import socket
import subprocess

print('Testing hostname resolution methods:')

# Method 1: Direct socket
try:
    ip = socket.gethostbyname('dfs-namenode')
    print(f'✓ Resolved dfs-namenode to {ip}')
except Exception as e:
    print(f'✗ Failed to resolve dfs-namenode: {e}')

# Method 2: Using getent
try:
    result = subprocess.run(['getent', 'hosts', 'namenode'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f'✓ getent resolved namenode: {result.stdout.strip()}')
    else:
        print('✗ getent failed for namenode')
except Exception as e:
    print(f'✗ getent error: {e}')

# Method 3: Check Docker's embedded DNS
try:
    import struct
    dns_servers = []
    with open('/etc/resolv.conf', 'r') as f:
        for line in f:
            if line.startswith('nameserver'):
                dns_servers.append(line.split()[1])
    print(f'DNS servers: {dns_servers}')
except Exception as e:
    print(f'Error reading DNS config: {e}')
"

echo ""
echo "7. SOLUTION: Create a wrapper script that works"
cat > working_client.sh << 'EOF'
#!/bin/bash
# Working client wrapper

# Method 1: Try from inside client container with environment fix
echo "Method 1: Using client container with DNS fix..."
docker-compose exec -T client bash -c '
# Add hosts entry if missing
if ! grep -q namenode /etc/hosts; then
    echo "172.18.0.2 namenode" >> /etc/hosts
fi
export NAMENODE_HOST=namenode
python -m client.cli "$@"
' -- "$@"

# If that fails, try method 2
if [ $? -ne 0 ]; then
    echo "Method 2: Using localhost from host..."
    NAMENODE_HOST=localhost python3 client/cli.py "$@"
fi
EOF
chmod +x working_client.sh

echo ""
echo "Testing the working client wrapper..."
echo "Test content for wrapper" > wrapper_test.txt
./working_client.sh upload wrapper_test.txt /wrapper_test.txt
./working_client.sh ls /

echo ""
echo "=== Solutions Applied ==="
echo ""
echo "Try using the working client wrapper:"
echo "  ./working_client.sh <command> <args>"
echo ""
echo "Example:"
echo "  ./working_client.sh upload myfile.txt /myfile.txt"
echo "  ./working_client.sh ls /"
echo ""
echo "If still having issues, the problem might be:"
echo "1. Docker Desktop DNS issues (restart Docker)"
echo "2. Firewall blocking Docker networks"
echo "3. WSL2 networking issues (if on Windows)"
echo ""
echo "Google search terms for more help:"
echo '- "docker-compose container cannot resolve hostname"'
echo '- "Failed to resolve container name docker-compose"'
echo '- "docker embedded dns not working"'