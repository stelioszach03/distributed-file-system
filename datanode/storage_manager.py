"""
Storage manager for DataNode.
Handles local chunk storage operations.
"""
import os
import shutil
from typing import Optional
from common.constants import DATANODE_STORAGE_PATH
from common.utils import setup_logger, ensure_directory, calculate_checksum


logger = setup_logger('StorageManager')


class StorageManager:
    """Manages local chunk storage on DataNode."""
    
    def __init__(self, node_id: str, storage_path: str = None):
        self.node_id = node_id
        self.storage_path = storage_path or os.path.join(DATANODE_STORAGE_PATH, node_id)
        ensure_directory(self.storage_path)
        logger.info(f"Storage manager initialized at {self.storage_path}")
    
    def store_chunk(self, chunk_id: str, data: bytes) -> str:
        """Store a chunk and return its checksum."""
        try:
            chunk_path = self._get_chunk_path(chunk_id)
            
            # Write chunk to disk
            with open(chunk_path, 'wb') as f:
                f.write(data)
            
            # Calculate and return checksum
            checksum = calculate_checksum(data)
            logger.info(f"Stored chunk {chunk_id} ({len(data)} bytes)")
            return checksum
            
        except Exception as e:
            logger.error(f"Failed to store chunk {chunk_id}: {e}")
            raise
    
    def retrieve_chunk(self, chunk_id: str) -> Optional[bytes]:
        """Retrieve a chunk by ID."""
        try:
            chunk_path = self._get_chunk_path(chunk_id)
            
            if not os.path.exists(chunk_path):
                logger.warning(f"Chunk {chunk_id} not found")
                return None
            
            with open(chunk_path, 'rb') as f:
                data = f.read()
            
            logger.info(f"Retrieved chunk {chunk_id} ({len(data)} bytes)")
            return data
            
        except Exception as e:
            logger.error(f"Failed to retrieve chunk {chunk_id}: {e}")
            raise
    
    def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a chunk."""
        try:
            chunk_path = self._get_chunk_path(chunk_id)
            
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
                logger.info(f"Deleted chunk {chunk_id}")
                return True
            
            logger.warning(f"Chunk {chunk_id} not found for deletion")
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete chunk {chunk_id}: {e}")
            return False
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics."""
        try:
            # Get disk usage
            stat = os.statvfs(self.storage_path)
            total_space = stat.f_blocks * stat.f_frsize
            available_space = stat.f_bavail * stat.f_frsize
            used_space = total_space - available_space
            
            # Count chunks
            chunk_count = len([f for f in os.listdir(self.storage_path) 
                             if f.endswith('.chunk')])
            
            return {
                'total_space': total_space,
                'available_space': available_space,
                'used_space': used_space,
                'chunk_count': chunk_count,
                'storage_path': self.storage_path
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                'total_space': 0,
                'available_space': 0,
                'used_space': 0,
                'chunk_count': 0,
                'storage_path': self.storage_path
            }
    
    def _get_chunk_path(self, chunk_id: str) -> str:
        """Get the file path for a chunk."""
        return os.path.join(self.storage_path, f"{chunk_id}.chunk")
    
    def list_chunks(self) -> list:
        """List all stored chunk IDs."""
        try:
            chunks = []
            for filename in os.listdir(self.storage_path):
                if filename.endswith('.chunk'):
                    chunk_id = filename[:-6]  # Remove .chunk extension
                    chunks.append(chunk_id)
            return chunks
        except Exception as e:
            logger.error(f"Failed to list chunks: {e}")
            return []