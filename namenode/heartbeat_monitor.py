"""
Heartbeat monitor for tracking DataNode health.
"""
import time
import threading
from typing import Dict, Callable
from common.constants import HEARTBEAT_TIMEOUT
from common.utils import setup_logger


logger = setup_logger('HeartbeatMonitor')


class HeartbeatMonitor:
    """Monitors DataNode heartbeats and detects failures."""
    
    def __init__(self, chunk_manager, failure_callback: Callable[[str], None]):
        self.chunk_manager = chunk_manager
        self.failure_callback = failure_callback
        self.last_heartbeat: Dict[str, float] = {}
        self.lock = threading.Lock()
        self.monitoring = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def record_heartbeat(self, node_id: str):
        """Record a heartbeat from a DataNode."""
        with self.lock:
            self.last_heartbeat[node_id] = time.time()
            logger.debug(f"Heartbeat received from {node_id}")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                current_time = time.time()
                failed_nodes = []
                
                with self.lock:
                    for node_id, last_beat in list(self.last_heartbeat.items()):
                        if current_time - last_beat > HEARTBEAT_TIMEOUT:
                            failed_nodes.append(node_id)
                
                # Handle failures outside of lock to avoid deadlock
                for node_id in failed_nodes:
                    logger.warning(f"DataNode {node_id} heartbeat timeout detected")
                    self.failure_callback(node_id)
                    with self.lock:
                        self.last_heartbeat.pop(node_id, None)
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
    
    def stop(self):
        """Stop the heartbeat monitor."""
        self.monitoring = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join()