"""
Chunk manager for the NameNode.
Handles chunk placement, replication, and recovery.
"""
import uuid
import random
import threading
import time
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from common.constants import REPLICATION_FACTOR, CHUNK_SIZE
from common.messages import ChunkInfo
from common.utils import setup_logger


logger = setup_logger('ChunkManager')


@dataclass
class DataNodeInfo:
    """Information about a DataNode."""
    node_id: str
    host: str
    port: int
    available_space: int
    used_space: int
    chunk_count: int
    last_heartbeat: float
    is_alive: bool = True


class ChunkManager:
    """Manages chunk placement and replication."""
    
    def __init__(self, metadata_manager):
        self.metadata_manager = metadata_manager
        self.datanodes: Dict[str, DataNodeInfo] = {}
        self.chunk_to_nodes: Dict[str, Set[str]] = {}  # chunk_id -> set of node_ids
        self.node_to_chunks: Dict[str, Set[str]] = {}  # node_id -> set of chunk_ids
        self.lock = threading.RLock()
        
        # Start replication monitor thread
        self.replication_thread = threading.Thread(target=self._monitor_replication, daemon=True)
        self.replication_thread.start()
    
    def register_datanode(self, node_id: str, host: str, port: int) -> DataNodeInfo:
        """Register a new DataNode."""
        with self.lock:
            datanode = DataNodeInfo(
                node_id=node_id,
                host=host,
                port=port,
                available_space=0,
                used_space=0,
                chunk_count=0,
                last_heartbeat=time.time()
            )
            self.datanodes[node_id] = datanode
            self.node_to_chunks[node_id] = set()
            
            logger.info(f"Registered DataNode: {node_id} at {host}:{port}")
            return datanode
    
    def update_datanode_info(self, node_id: str, available_space: int, used_space: int, 
                           chunk_count: int):
        """Update DataNode information from heartbeat."""
        with self.lock:
            if node_id in self.datanodes:
                datanode = self.datanodes[node_id]
                datanode.available_space = available_space
                datanode.used_space = used_space
                datanode.chunk_count = chunk_count
                datanode.last_heartbeat = time.time()
                datanode.is_alive = True
    
    def allocate_chunk(self, size: int, replication_factor: int = REPLICATION_FACTOR) -> Tuple[str, List[str]]:
        """Allocate a new chunk and select DataNodes for storage."""
        with self.lock:
            chunk_id = str(uuid.uuid4())
            
            # Select DataNodes for chunk placement
            selected_nodes = self._select_datanodes_for_chunk(size, replication_factor)
            
            if len(selected_nodes) < replication_factor:
                logger.warning(f"Only {len(selected_nodes)} nodes available for replication factor {replication_factor}")
            
            # Update mappings
            self.chunk_to_nodes[chunk_id] = set(selected_nodes)
            for node_id in selected_nodes:
                self.node_to_chunks[node_id].add(chunk_id)
            
            logger.info(f"Allocated chunk {chunk_id} to nodes: {selected_nodes}")
            return chunk_id, selected_nodes
    
    def _select_datanodes_for_chunk(self, size: int, replication_factor: int) -> List[str]:
        """Select DataNodes for chunk placement using a simple strategy."""
        available_nodes = []
        
        for node_id, node_info in self.datanodes.items():
            if node_info.is_alive and node_info.available_space >= size:
                available_nodes.append((node_id, node_info.available_space))
        
        # Sort by available space (descending) and select top nodes
        available_nodes.sort(key=lambda x: x[1], reverse=True)
        selected = [node_id for node_id, _ in available_nodes[:replication_factor]]
        
        return selected
    
    def get_chunk_locations(self, chunk_id: str) -> List[str]:
        """Get DataNode locations for a chunk."""
        with self.lock:
            return list(self.chunk_to_nodes.get(chunk_id, set()))
    
    def report_chunk_stored(self, chunk_id: str, node_id: str):
        """Report that a chunk has been successfully stored on a DataNode."""
        with self.lock:
            if chunk_id not in self.chunk_to_nodes:
                self.chunk_to_nodes[chunk_id] = set()
            self.chunk_to_nodes[chunk_id].add(node_id)
            
            if node_id not in self.node_to_chunks:
                self.node_to_chunks[node_id] = set()
            self.node_to_chunks[node_id].add(chunk_id)
            
            # Update chunk metadata
            self.metadata_manager.update_chunk_replicas(
                chunk_id, 
                list(self.chunk_to_nodes[chunk_id])
            )
    
    def handle_datanode_failure(self, node_id: str):
        """Handle DataNode failure and trigger re-replication."""
        with self.lock:
            if node_id not in self.datanodes:
                return
            
            self.datanodes[node_id].is_alive = False
            logger.warning(f"DataNode {node_id} marked as failed")
            
            # Get chunks that need re-replication
            affected_chunks = self.node_to_chunks.get(node_id, set()).copy()
            
            # Remove node from chunk mappings
            for chunk_id in affected_chunks:
                if chunk_id in self.chunk_to_nodes:
                    self.chunk_to_nodes[chunk_id].discard(node_id)
            
            # Clear node's chunk list
            self.node_to_chunks[node_id] = set()
            
            # Trigger re-replication for affected chunks
            for chunk_id in affected_chunks:
                self._schedule_replication(chunk_id)
    
    def _schedule_replication(self, chunk_id: str):
        """Schedule chunk for re-replication."""
        current_replicas = len(self.chunk_to_nodes.get(chunk_id, set()))
        chunk_info = self.metadata_manager.get_chunk(chunk_id)
        
        if chunk_info and current_replicas < chunk_info.replication_factor:
            logger.info(f"Scheduling replication for chunk {chunk_id}: "
                       f"{current_replicas}/{chunk_info.replication_factor} replicas")
            # In a real system, this would trigger actual replication
    
    def _monitor_replication(self):
        """Monitor and maintain replication factor for all chunks."""
        while True:
            try:
                time.sleep(10)  # Check every 10 seconds
                
                with self.lock:
                    # Check for dead DataNodes
                    current_time = time.time()
                    for node_id, node_info in self.datanodes.items():
                        if node_info.is_alive and current_time - node_info.last_heartbeat > 30:
                            logger.warning(f"DataNode {node_id} heartbeat timeout")
                            self.handle_datanode_failure(node_id)
                    
                    # Check replication factor for all chunks
                    for chunk_id, node_ids in self.chunk_to_nodes.items():
                        chunk_info = self.metadata_manager.get_chunk(chunk_id)
                        if chunk_info:
                            alive_replicas = sum(1 for node_id in node_ids 
                                               if self.datanodes.get(node_id, {}).get('is_alive', False))
                            
                            if alive_replicas < chunk_info.replication_factor:
                                self._schedule_replication(chunk_id)
                
            except Exception as e:
                logger.error(f"Error in replication monitor: {e}")
    
    def get_cluster_stats(self) -> Dict:
        """Get cluster statistics."""
        with self.lock:
            total_nodes = len(self.datanodes)
            alive_nodes = sum(1 for node in self.datanodes.values() if node.is_alive)
            total_space = sum(node.available_space + node.used_space 
                            for node in self.datanodes.values())
            used_space = sum(node.used_space for node in self.datanodes.values())
            total_chunks = len(self.chunk_to_nodes)
            
            return {
                'total_nodes': total_nodes,
                'alive_nodes': alive_nodes,
                'dead_nodes': total_nodes - alive_nodes,
                'total_space': total_space,
                'used_space': used_space,
                'available_space': total_space - used_space,
                'total_chunks': total_chunks,
                'usage_percentage': (used_space / total_space * 100) if total_space > 0 else 0
            }