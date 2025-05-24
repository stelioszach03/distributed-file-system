#!/bin/bash
# Complete fix script for the distributed file system

echo "=== Complete Fix for Distributed File System ==="
echo ""

# Stop all services first
echo "Stopping all services..."
docker-compose down

# Fix both client/api_client.py and namenode/file_handlers.py
echo "Fixing client/api_client.py..."
cp client/api_client.py client/api_client.py.backup 2>/dev/null || true

# Create fixed version directly from the document content
cat > client/api_client.py << 'CLIENTEOF'
"""
API client library for interacting with the distributed file system.
"""
import os
import requests
from typing import List, Dict, Optional
from common.constants import NAMENODE_HOST, NAMENODE_API_PORT, CHUNK_SIZE, API_TIMEOUT
from common.utils import setup_logger, split_file_into_chunks, merge_chunks, calculate_checksum


logger = setup_logger('DFSClient')


class DFSClient:
    """Client library for distributed file system operations."""
    
    def __init__(self, namenode_host: str = NAMENODE_HOST, 
                 namenode_port: int = NAMENODE_API_PORT):
        self.namenode_url = f"http://{namenode_host}:{namenode_port}"
        self.session = requests.Session()
    
    def create_file(self, path: str, replication_factor: int = 3) -> Dict:
        """Create a new file in the DFS."""
        try:
            response = self.session.post(
                f"{self.namenode_url}/files",
                json={'path': path, 'replication_factor': replication_factor}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create file {path}: {e}")
            raise
    
    def upload_file(self, local_path: str, dfs_path: str, replication_factor: int = 3):
        """Upload a local file to the DFS."""
        try:
            # Create file entry
            self.create_file(dfs_path, replication_factor)
            
            # Split file into chunks
            file_size = os.path.getsize(local_path)
            total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
            
            logger.info(f"Uploading {local_path} ({file_size} bytes) in {total_chunks} chunks")
            
            with open(local_path, 'rb') as f:
                chunk_index = 0
                while True:
                    chunk_data = f.read(CHUNK_SIZE)
                    if not chunk_data:
                        break
                    
                    # Allocate chunk
                    allocation = self._allocate_chunk(len(chunk_data), replication_factor)
                    chunk_id = allocation['chunk_id']
                    locations = allocation['locations']
                    
                    # Upload to primary location
                    if locations:
                        primary_node = locations[0]
                        self._upload_chunk_to_node(chunk_id, chunk_data, primary_node)
                        
                        # Trigger replication to other nodes
                        if len(locations) > 1:
                            self._trigger_replication(chunk_id, primary_node, locations[1:])
                    
                    # Mark chunk as complete
                    checksum = calculate_checksum(chunk_data)
                    self._complete_chunk(chunk_id, dfs_path, len(chunk_data), checksum)
                    
                    chunk_index += 1
                    logger.info(f"Uploaded chunk {chunk_index}/{total_chunks}")
            
            logger.info(f"Successfully uploaded {local_path} to {dfs_path}")
            
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            # Clean up on failure
            try:
                self.delete_file(dfs_path)
            except:
                pass
            raise
    
    def download_file(self, dfs_path: str, local_path: str):
        """Download a file from the DFS."""
        try:
            # Get file metadata
            file_info = self.get_file_info(dfs_path)
            if not file_info:
                raise FileNotFoundError(f"File not found: {dfs_path}")
            
            logger.info(f"Downloading {dfs_path} ({file_info['size']} bytes)")
            
            # Download chunks
            chunks_data = []
            for i, chunk_info in enumerate(file_info['chunks']):
                chunk_id = chunk_info['chunk_id']
                locations = chunk_info['locations']
                
                if not locations:
                    raise Exception(f"No locations available for chunk {chunk_id}")
                
                # Try to download from first available location
                chunk_data = None
                for location in locations:
                    try:
                        chunk_data = self._download_chunk_from_node(chunk_id, location)
                        if chunk_data:
                            break
                    except Exception as e:
                        logger.warning(f"Failed to download from {location}: {e}")
                
                if not chunk_data:
                    raise Exception(f"Failed to download chunk {chunk_id}")
                
                chunks_data.append(chunk_data)
                logger.info(f"Downloaded chunk {i+1}/{len(file_info['chunks'])}")
            
            # Merge chunks into file
            merge_chunks(chunks_data, local_path)
            logger.info(f"Successfully downloaded {dfs_path} to {local_path}")
            
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise
    
    def delete_file(self, path: str):
        """Delete a file from the DFS."""
        try:
            response = self.session.delete(f"{self.namenode_url}/files{path}")
            response.raise_for_status()
            logger.info(f"Deleted file: {path}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete file {path}: {e}")
            raise
    
    def list_directory(self, path: str = '/') -> List[Dict]:
        """List contents of a directory."""
        try:
            response = self.session.get(f"{self.namenode_url}/directories{path}")
            response.raise_for_status()
            return response.json()['contents']
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list directory {path}: {e}")
            raise
    
    def create_directory(self, path: str):
        """Create a directory."""
        try:
            response = self.session.post(
                f"{self.namenode_url}/directories",
                json={'path': path}
            )
            response.raise_for_status()
            logger.info(f"Created directory: {path}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create directory {path}: {e}")
            raise
    
    def get_file_info(self, path: str) -> Optional[Dict]:
        """Get file metadata."""
        try:
            response = self.session.get(f"{self.namenode_url}/files{path}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get file info for {path}: {e}")
            raise
    
    def get_cluster_stats(self) -> Dict:
        """Get cluster statistics."""
        try:
            response = self.session.get(f"{self.namenode_url}/cluster/stats")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get cluster stats: {e}")
            raise
    
    def _allocate_chunk(self, size: int, replication_factor: int) -> Dict:
        """Allocate a new chunk."""
        response = self.session.post(
            f"{self.namenode_url}/chunks/allocate",
            json={'size': size, 'replication_factor': replication_factor}
        )
        response.raise_for_status()
        return response.json()
    
    def _upload_chunk_to_node(self, chunk_id: str, data: bytes, node_id: str):
        """Upload chunk data to a specific DataNode."""
        try:
            # node_id is already the correct hostname like "datanode-1"
            # Extract the number to calculate the port
            node_number = int(node_id.split('-')[-1])
            api_port = 8081 + (node_number - 1)
            
            # Use the node_id directly as hostname
            datanode_url = f"http://{node_id}:{api_port}"
            
            response = self.session.put(
                f"{datanode_url}/chunks/{chunk_id}",
                data=data,
                headers={'Content-Type': 'application/octet-stream'},
                timeout=API_TIMEOUT
            )
            response.raise_for_status()
            logger.info(f"Successfully uploaded chunk {chunk_id} to {node_id}")
            
        except Exception as e:
            logger.error(f"Failed to upload chunk {chunk_id} to {node_id}: {e}")
            raise
    
    def _download_chunk_from_node(self, chunk_id: str, node_id: str) -> bytes:
        """Download chunk data from a specific DataNode."""
        try:
            # Extract node number and calculate port
            node_number = int(node_id.split('-')[-1])
            api_port = 8081 + (node_number - 1)
            
            # Use the node_id directly as hostname
            datanode_url = f"http://{node_id}:{api_port}"
            
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
            # Extract node number and calculate port
            node_number = int(source_node.split('-')[-1])
            api_port = 8081 + (node_number - 1)
            
            datanode_url = f"http://{source_node}:{api_port}"
            
            # Prepare target node information
            targets = []
            for target_id in target_nodes:
                target_number = int(target_id.split('-')[-1])
                target_api_port = 8081 + (target_number - 1)
                targets.append({
                    'node_id': target_id,
                    'host': target_id,  # Use node_id as hostname
                    'api_port': target_api_port
                })
            
            response = self.session.post(
                f"{datanode_url}/replicate",
                json={
                    'chunk_id': chunk_id,
                    'target_nodes': targets
                }
            )
            response.raise_for_status()
            logger.info(f"Triggered replication of chunk {chunk_id} from {source_node} to {target_nodes}")
            
        except Exception as e:
            logger.error(f"Failed to trigger replication: {e}")
    
    def _complete_chunk(self, chunk_id: str, file_path: str, size: int, checksum: str):
        """Mark chunk upload as complete."""
        response = self.session.post(
            f"{self.namenode_url}/chunks/{chunk_id}/complete",
            json={
                'file_path': file_path,
                'size': size,
                'checksum': checksum
            }
        )
        response.raise_for_status()
CLIENTEOF

echo "Fixing namenode/file_handlers.py..."
cp namenode/file_handlers.py namenode/file_handlers.py.backup 2>/dev/null || true

# The key fix is in how we handle the node_id
sed -i 's/datanode_url = f"http:\/\/datanode-{node_id}:{api_port}"/datanode_url = f"http:\/\/{node_id}:{api_port}"/g' namenode/file_handlers.py

# Also need to ensure metadata_manager doesn't cause issues
echo "Checking namenode/metadata_manager.py..."
# Make sure parent directory check doesn't fail for root paths
sed -i '/ parent_path != .\/.\ and parent_path not in self.directories:/s/parent_path != .\/.\ and/parent_path != .\/.\ and parent_path != "" and/' namenode/metadata_manager.py 2>/dev/null || true

# Rebuild containers to ensure changes are applied
echo ""
echo "Rebuilding containers..."
docker-compose build namenode datanode1 datanode2 datanode3 client

# Start services
echo ""
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready (20 seconds)..."
sleep 20

# Create test directory first
echo ""
echo "Creating test directory..."
docker-compose exec -T client python -m client.cli mkdir /tests || true

# Test the system
echo ""
echo "Testing file upload..."
docker-compose exec -T client bash -c "echo 'Testing complete fix!' > /workspace/test_complete.txt"
docker-compose exec -T client python -m client.cli upload /workspace/test_complete.txt /tests/complete.txt

echo ""
echo "Checking uploaded file..."
docker-compose exec -T client python -m client.cli ls /tests

echo ""
echo "Testing file download..."
docker-compose exec -T client python -m client.cli download /tests/complete.txt /workspace/downloaded_complete.txt
docker-compose exec -T client cat /workspace/downloaded_complete.txt

echo ""
echo "=== Complete Fix Applied ==="
echo ""
echo "The system should now be working correctly."
echo "You can access:"
echo "• Web UI: http://localhost:3001"
echo "• Grafana: http://localhost:3000 (admin/admin)"
echo "• NameNode API: http://localhost:8080"
echo ""
echo "To run full tests: ./test_system.sh"
echo "To see a demo: ./demo.sh"