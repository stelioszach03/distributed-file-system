#!/bin/bash
# Run DFS operations from host machine

echo "=== Running DFS Client from Host ==="
echo ""

# Install Python dependencies if needed
echo "Installing Python dependencies..."
pip3 install --user requests tabulate 2>/dev/null || sudo pip3 install requests tabulate

# Create a wrapper script
cat > dfs_host_client.py << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Set the NAMENODE_HOST to localhost since we're running from host
os.environ['NAMENODE_HOST'] = 'localhost'

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the CLI
from client.cli import main

if __name__ == '__main__':
    sys.exit(main())
EOF

chmod +x dfs_host_client.py

# Create test files
echo "Creating test files..."
echo "Test from host machine!" > test_from_host.txt
dd if=/dev/urandom of=test_large_from_host.dat bs=1M count=2 2>/dev/null

# Test operations
echo ""
echo "Testing file operations from host..."

echo "1. Checking cluster status:"
python3 dfs_host_client.py stats

echo ""
echo "2. Creating directory:"
python3 dfs_host_client.py mkdir /host_test

echo ""
echo "3. Uploading files:"
python3 dfs_host_client.py upload test_from_host.txt /host_test/test.txt
python3 dfs_host_client.py upload test_large_from_host.dat /host_test/large.dat

echo ""
echo "4. Listing files:"
python3 dfs_host_client.py ls /host_test

echo ""
echo "5. Downloading file:"
python3 dfs_host_client.py download /host_test/test.txt downloaded_test.txt
echo "Downloaded content:"
cat downloaded_test.txt

# Clean up
rm -f test_from_host.txt test_large_from_host.dat downloaded_test.txt

echo ""
echo "=== Host Client Setup Complete ==="
echo ""
echo "You can now use the DFS client from your host machine:"
echo "  ./dfs_host_client.py <command> <args>"
echo ""
echo "Examples:"
echo "  ./dfs_host_client.py ls /"
echo "  ./dfs_host_client.py upload myfile.txt /myfile.txt"
echo "  ./dfs_host_client.py download /myfile.txt downloaded.txt"
echo "  ./dfs_host_client.py stats"