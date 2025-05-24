"""
Protocol messages for communication between components.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import json


class MessageType(Enum):
    # Heartbeat messages
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"
    
    # File operation messages
    CREATE_FILE = "create_file"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    LIST_DIR = "list_dir"
    
    # Chunk messages
    ALLOCATE_CHUNK = "allocate_chunk"
    REPLICATE_CHUNK = "replicate_chunk"
    DELETE_CHUNK = "delete_chunk"
    
    # Response messages
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class Message:
    """Base message class."""
    type: MessageType
    payload: Dict
    
    def to_json(self) -> str:
        """Serialize message to JSON."""
        return json.dumps({
            'type': self.type.value,
            'payload': self.payload
        })
    
    @classmethod
    def from_json(cls, data: str) -> 'Message':
        """Deserialize message from JSON."""
        obj = json.loads(data)
        return cls(
            type=MessageType(obj['type']),
            payload=obj['payload']
        )


@dataclass
class HeartbeatMessage:
    """Heartbeat message from DataNode to NameNode."""
    node_id: str
    available_space: int
    used_space: int
    chunk_count: int
    cpu_usage: float
    memory_usage: float
    timestamp: float


@dataclass
class ChunkInfo:
    """Information about a chunk."""
    chunk_id: str
    size: int
    checksum: str
    replicas: List[str]  # List of DataNode IDs


@dataclass
class FileInfo:
    """Information about a file."""
    path: str
    size: int
    chunks: List[str]  # List of chunk IDs
    created_at: float
    modified_at: float
    replication_factor: int