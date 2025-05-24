"""
Replication manager for DataNode.
Handles chunk replication between DataNodes.
"""
import threading
import requests
import time
from typing import List, Optional
from common.constants import DATANODE_API_PORT, API_TIMEOUT
from common.utils import setup_logger, calculate_checksum


logger = setup_logger('ReplicationManager')


class ReplicationManager:
    """Manages chunk replication between DataNodes."""
    
    def __init__(self, storage_manager, node_id: str):
        self.storage_manager = storage_manager
        self.node_id = node_id
        self.replication_queue = []
        self.lock = threading.Lock()
        self.running = True
        
        # Start replication worker thread
        self.worker_thread = threading.Thread(target=self._replication_worker, daemon=True)
        self.worker_thread.start()
    
    def replicate_chunk(self, chunk_id: str, target_nodes: List[dict]):
        """Add chunk to replication queue."""
        with self.lock:
            self.replication_queue.append({
                'chunk_id': chunk_id,
                'target_nodes': target_nodes,
                'attempts': 0
            })
        logger.info(f"Queued chunk {chunk_id} for replication to {len(target_nodes)} nodes")
    
    def _replication_worker(self):
        """Worker thread for processing replication queue."""
        while self.running:
            try:
                # Get next replication task
                task = None
                with self.lock:
                    if self.replication_queue:
                        task = self.replication_queue.pop(0)
                
                if task:
                    self._process_replication(task)
                else:
                    time.sleep(1)  # No tasks, wait
                    
            except Exception as e:
                logger.error(f"Error in replication worker: {e}")
    
    def _process_replication(self, task: dict):
        """Process a single replication task."""
        chunk_id = task['chunk_id']
        target_nodes = task['target_nodes']
        
        # Retrieve chunk data
        chunk_data = self.storage_manager.retrieve_chunk(chunk_id)
        if not chunk_data:
            logger.error(f"Failed to retrieve chunk {chunk_id} for replication")
            return
        
        # Replicate to each target node
        success_count = 0
        for node in target_nodes:
            if self._replicate_to_node(chunk_id, chunk_data, node):
                success_count += 1
        
        logger.info(f"Replicated chunk {chunk_id} to {success_count}/{len(target_nodes)} nodes")
        
        # Retry failed replications
        if success_count < len(target_nodes) and task['attempts'] < 3:
            task['attempts'] += 1
            failed_nodes = [n for n in target_nodes 
                          if not self._check_chunk_exists(chunk_id, n)]
            if failed_nodes:
                task['target_nodes'] = failed_nodes
                with self.lock:
                    self.replication_queue.append(task)
    
    def _replicate_to_node(self, chunk_id: str, data: bytes, node: dict) -> bool:
        """Replicate chunk to a specific node."""
        try:
            url = f"http://{node['host']}:{node.get('api_port', DATANODE_API_PORT)}/chunks/{chunk_id}"
            
            response = requests.put(
                url,
                data=data,
                headers={'Content-Type': 'application/octet-stream'},
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully replicated chunk {chunk_id} to {node['node_id']}")
                return True
            else:
                logger.error(f"Failed to replicate chunk {chunk_id} to {node['node_id']}: "
                           f"{response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error replicating chunk {chunk_id} to {node['node_id']}: {e}")
            return False
    
    def _check_chunk_exists(self, chunk_id: str, node: dict) -> bool:
        """Check if chunk exists on a node."""
        try:
            url = f"http://{node['host']}:{node.get('api_port', DATANODE_API_PORT)}/chunks/{chunk_id}/exists"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def stop(self):
        """Stop the replication manager."""
        self.running = False
        if self.worker_thread.is_alive():
            self.worker_thread.join()