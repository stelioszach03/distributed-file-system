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
        # In a real implementation, we'd need node host/port info
        # For now, assuming DataNodes are addressable by ID
        datanode_url = f"http://datanode-{node_id}:8081"
        
        response = self.session.put(
            f"{datanode_url}/chunks/{chunk_id}",
            data=data,
            headers={'Content-Type': 'application/octet-stream'},
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
    
    def _download_chunk_from_node(self, chunk_id: str, node_id: str) -> bytes:
        """Download chunk data from a specific DataNode."""
        datanode_url = f"http://datanode-{node_id}:8081"
        
        response = self.session.get(
            f"{datanode_url}/chunks/{chunk_id}",
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
        return response.content
    
    def _trigger_replication(self, chunk_id: str, source_node: str, target_nodes: List[str]):
        """Trigger chunk replication from source to target nodes."""
        datanode_url = f"http://datanode-{source_node}:8081"
        
        response = self.session.post(
            f"{datanode_url}/replicate",
            json={
                'chunk_id': chunk_id,
                'target_nodes': [{'node_id': node} for node in target_nodes]
            }
        )
        response.raise_for_status()
    
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