#!/bin/bash
# Manual fix script - step by step

echo "=== Manual Fix for Upload Issue ==="
echo ""

# Step 1: Check current issues
echo "Step 1: Checking current issues..."
echo "Testing chunk allocation..."
ALLOCATION_RESULT=$(curl -s -X POST http://localhost:8080/chunks/allocate \
  -H "Content-Type: application/json" \
  -d '{"size": 1024, "replication_factor": 1}' 2>&1)

echo "$ALLOCATION_RESULT" | python3 -m json.tool 2>/dev/null || echo "Allocation failed: $ALLOCATION_RESULT"
echo ""

# Extract a node_id from the result to see the format
NODE_ID=$(echo "$ALLOCATION_RESULT" | grep -o '"locations":\s*\[[^]]*\]' | grep -o '"[^"]*"' | grep -v "locations" | head -1 | tr -d '"')
echo "Sample node_id from allocation: '$NODE_ID'"
echo ""

# Step 2: Apply targeted fix based on the node_id format
echo "Step 2: Applying targeted fix..."

# Check if the problem is double prefix
if [[ "$NODE_ID" == *"datanode-datanode"* ]]; then
    echo "Found double prefix issue. Fixing chunk_manager.py..."
    
    # Fix the chunk_manager.py to not add extra prefix
    docker-compose exec -T namenode python -c "
import re
with open('/app/namenode/chunk_manager.py', 'r') as f:
    content = f.read()
# Look for where node_id might be getting prefixed
content = re.sub(r'datanode-[\"\']\s*\+\s*', '', content)
with open('/app/namenode/chunk_manager.py', 'w') as f:
    f.write(content)
print('Fixed chunk_manager.py')
"
fi

# Step 3: Create a properly fixed client
echo ""
echo "Step 3: Creating fixed client/api_client.py..."

# Create a test to see the actual format
docker-compose exec -T client python -c "
import sys
sys.path.insert(0, '/app')
from client.api_client import DFSClient
client = DFSClient()
try:
    result = client._allocate_chunk(1024, 1)
    print('Allocation result:', result)
    if result.get('locations'):
        node_id = result['locations'][0]
        print(f'Node ID format: {node_id}')
        # Determine the correct hostname
        if node_id.startswith('datanode-datanode-'):
            # Double prefix
            parts = node_id.split('-')
            number = parts[-1]
            hostname = f'datanode-{number}'
        elif node_id.startswith('datanode-'):
            # Correct format
            hostname = node_id
        else:
            # Just the node id without prefix
            hostname = f'datanode-{node_id}'
        print(f'Correct hostname should be: {hostname}')
except Exception as e:
    print(f'Error: {e}')
"

# Apply the comprehensive fix
docker-compose exec -T client bash -c 'cat > /app/client/api_client_fixed.py << "FIXEOF"
"""
API client library for interacting with the distributed file system.
"""
import os
import requests
from typing import List, Dict, Optional
from common.constants import NAMENODE_HOST, NAMENODE_API_PORT, CHUNK_SIZE, API_TIMEOUT
from common.utils import setup_logger, split_file_into_chunks, merge_chunks, calculate_checksum


logger = setup_logger("DFSClient")


class DFSClient:
    """Client library for distributed file system operations."""
    
    def __init__(self, namenode_host: str = NAMENODE_HOST, 
                 namenode_port: int = NAMENODE_API_PORT):
        self.namenode_url = f"http://{namenode_host}:{namenode_port}"
        self.session = requests.Session()
    
    def _fix_node_id(self, node_id: str) -> str:
        """Fix node_id format issues."""
        # Handle various formats we might receive
        if node_id.startswith("datanode-datanode-"):
            # Double prefix issue
            parts = node_id.split("-")
            return f"datanode-{parts[-1]}"
        elif node_id.startswith("datanode-"):
            # Already correct
            return node_id
        else:
            # Just a number or other format
            try:
                num = int(node_id)
                return f"datanode-{num}"
            except:
                # Fallback - assume it'"'"'s the correct hostname
                return node_id
    
    def _upload_chunk_to_node(self, chunk_id: str, data: bytes, node_id: str):
        """Upload chunk data to a specific DataNode."""
        try:
            # Fix the node_id format
            hostname = self._fix_node_id(node_id)
            
            # Extract number for port calculation
            node_number = int(hostname.split("-")[-1])
            api_port = 8081 + (node_number - 1)
            
            datanode_url = f"http://{hostname}:{api_port}"
            
            logger.info(f"Uploading to {datanode_url}/chunks/{chunk_id}")
            
            response = self.session.put(
                f"{datanode_url}/chunks/{chunk_id}",
                data=data,
                headers={"Content-Type": "application/octet-stream"},
                timeout=API_TIMEOUT
            )
            response.raise_for_status()
            logger.info(f"Successfully uploaded chunk {chunk_id} to {hostname}")
            
        except Exception as e:
            logger.error(f"Failed to upload chunk {chunk_id} to {node_id} (fixed: {hostname}): {e}")
            raise
    
    def _download_chunk_from_node(self, chunk_id: str, node_id: str) -> bytes:
        """Download chunk data from a specific DataNode."""
        try:
            hostname = self._fix_node_id(node_id)
            node_number = int(hostname.split("-")[-1])
            api_port = 8081 + (node_number - 1)
            
            datanode_url = f"http://{hostname}:{api_port}"
            
            response = self.session.get(
                f"{datanode_url}/chunks/{chunk_id}",
                timeout=API_TIMEOUT
            )
            response.raise_for_status()
            return response.content
            
        except Exception as e:
            logger.error(f"Error downloading chunk {chunk_id} from {node_id}: {e}")
            return None
    
    def _trigger_replication(self, chunk_id: str, source_node: str, target_nodes: List[str]):
        """Trigger chunk replication from source to target nodes."""
        try:
            hostname = self._fix_node_id(source_node)
            node_number = int(hostname.split("-")[-1])
            api_port = 8081 + (node_number - 1)
            
            datanode_url = f"http://{hostname}:{api_port}"
            
            # Prepare target node information
            targets = []
            for target_id in target_nodes:
                target_hostname = self._fix_node_id(target_id)
                target_number = int(target_hostname.split("-")[-1])
                target_api_port = 8081 + (target_number - 1)
                targets.append({
                    "node_id": target_hostname,
                    "host": target_hostname,
                    "api_port": target_api_port
                })
            
            response = self.session.post(
                f"{datanode_url}/replicate",
                json={
                    "chunk_id": chunk_id,
                    "target_nodes": targets
                }
            )
            response.raise_for_status()
            logger.info(f"Triggered replication of chunk {chunk_id} from {hostname} to {target_nodes}")
            
        except Exception as e:
            logger.error(f"Failed to trigger replication: {e}")
FIXEOF'

# Copy over the rest of the methods
docker-compose exec -T client bash -c 'tail -n +250 /app/client/api_client.py >> /app/client/api_client_fixed.py'
docker-compose exec -T client bash -c 'mv /app/client/api_client_fixed.py /app/client/api_client.py'

echo ""
echo "Step 4: Testing the fix..."
docker-compose exec -T client bash -c "echo 'Manual fix test' > /workspace/manual_test.txt"
docker-compose exec -T client python -m client.cli upload /workspace/manual_test.txt /manual_test.txt

echo ""
echo "Step 5: Checking result..."
docker-compose exec -T client python -m client.cli ls /

echo ""
echo "=== Manual Fix Complete ==="
echo ""
echo "If the upload worked, the system is now fixed!"
echo "If not, run ./debug_system.sh to see what's wrong."