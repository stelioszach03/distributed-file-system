"""
Health reporter for DataNode.
Reports metrics and health status to monitoring systems.
"""
import psutil
import time
from prometheus_client import Gauge, Counter, Histogram
from common.utils import setup_logger


logger = setup_logger('HealthReporter')


# Prometheus metrics
storage_used = Gauge('dfs_datanode_storage_used_bytes', 'Used storage in bytes')
storage_available = Gauge('dfs_datanode_storage_available_bytes', 'Available storage in bytes')
chunk_count = Gauge('dfs_datanode_chunk_count', 'Number of chunks stored')
cpu_usage = Gauge('dfs_datanode_cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('dfs_datanode_memory_usage_percent', 'Memory usage percentage')
chunk_operations = Counter('dfs_datanode_chunk_operations_total', 'Total chunk operations', ['operation'])
operation_duration = Histogram('dfs_datanode_operation_duration_seconds', 'Operation duration', ['operation'])


class HealthReporter:
    """Reports health metrics for DataNode."""
    
    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        self.start_time = time.time()
    
    def get_health_status(self) -> dict:
        """Get current health status."""
        try:
            # Get storage stats
            storage_stats = self.storage_manager.get_storage_stats()
            
            # Get system stats
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            health_data = {
                'node_id': self.storage_manager.node_id,
                'uptime': time.time() - self.start_time,
                'storage': {
                    'used': storage_stats['used_space'],
                    'available': storage_stats['available_space'],
                    'total': storage_stats['total_space'],
                    'chunk_count': storage_stats['chunk_count']
                },
                'system': {
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory.percent,
                    'memory_available': memory.available
                },
                'timestamp': time.time()
            }
            
            # Update Prometheus metrics
            self._update_metrics(health_data)
            
            return health_data
            
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {
                'node_id': self.storage_manager.node_id,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _update_metrics(self, health_data: dict):
        """Update Prometheus metrics."""
        try:
            storage_used.set(health_data['storage']['used'])
            storage_available.set(health_data['storage']['available'])
            chunk_count.set(health_data['storage']['chunk_count'])
            cpu_usage.set(health_data['system']['cpu_usage'])
            memory_usage.set(health_data['system']['memory_usage'])
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
    
    def record_operation(self, operation: str, duration: float):
        """Record an operation for metrics."""
        chunk_operations.labels(operation=operation).inc()
        operation_duration.labels(operation=operation).observe(duration)