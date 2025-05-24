"""
Common utility functions.
"""
import hashlib
import os
import socket
from typing import List, Tuple
import logging


def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """Set up a logger with consistent formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def calculate_checksum(data: bytes) -> str:
    """Calculate SHA256 checksum of data."""
    return hashlib.sha256(data).hexdigest()


def split_file_into_chunks(file_path: str, chunk_size: int) -> List[bytes]:
    """Split a file into chunks of specified size."""
    chunks = []
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunks.append(chunk)
    return chunks


def merge_chunks(chunks: List[bytes], output_path: str):
    """Merge chunks back into a file."""
    with open(output_path, 'wb') as f:
        for chunk in chunks:
            f.write(chunk)


def get_free_port() -> int:
    """Get a free port on the system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def format_bytes(size: int) -> str:
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def ensure_directory(path: str):
    """Ensure directory exists."""
    os.makedirs(path, exist_ok=True)