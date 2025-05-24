"""
Constants used across the distributed file system.
"""
import os

# Network configuration
NAMENODE_HOST = os.environ.get('NAMENODE_HOST', 'namenode')
NAMENODE_PORT = 9870
NAMENODE_API_PORT = 8080
DATANODE_PORT = 9866
DATANODE_API_PORT = 8081

# Storage configuration
CHUNK_SIZE = 64 * 1024 * 1024  # 64MB chunks
REPLICATION_FACTOR = 3
DATANODE_STORAGE_PATH = '/data/dfs'

# Heartbeat configuration
HEARTBEAT_INTERVAL = 3  # seconds
HEARTBEAT_TIMEOUT = 10  # seconds
HEARTBEAT_RETRY_COUNT = 3

# API configuration
API_TIMEOUT = 30  # seconds
MAX_UPLOAD_SIZE = 1024 * 1024 * 1024  # 1GB

# Monitoring
METRICS_PORT = 9090
PROMETHEUS_NAMESPACE = 'dfs'