"""
Metadata manager for the NameNode.
Handles file system namespace and metadata operations.
"""
import os
import time
import json
import threading
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from common.messages import FileInfo, ChunkInfo
from common.utils import setup_logger


logger = setup_logger('MetadataManager')


@dataclass
class Directory:
    """Directory metadata."""
    path: str
    created_at: float
    modified_at: float
    children: Set[str]  # Set of child paths (files and directories)


class MetadataManager:
    """Manages file system metadata and namespace."""
    
    def __init__(self, persistence_path: str = '/data/namenode/metadata'):
        self.persistence_path = persistence_path
        self.files: Dict[str, FileInfo] = {}
        self.directories: Dict[str, Directory] = {}
        self.chunks: Dict[str, ChunkInfo] = {}
        self.lock = threading.RLock()
        
        # Initialize root directory
        self.directories['/'] = Directory(
            path='/',
            created_at=time.time(),
            modified_at=time.time(),
            children=set()
        )
        
        # Load persisted metadata
        self._load_metadata()
    
    def create_file(self, path: str, size: int = 0, replication_factor: int = 3) -> FileInfo:
        """Create a new file entry."""
        with self.lock:
            if path in self.files:
                raise FileExistsError(f"File already exists: {path}")
            
            # Ensure parent directory exists
            parent_path = os.path.dirname(path)
            if parent_path != '/' and parent_path not in self.directories:
                raise FileNotFoundError(f"Parent directory not found: {parent_path}")
            
            # Create file metadata
            file_info = FileInfo(
                path=path,
                size=size,
                chunks=[],
                created_at=time.time(),
                modified_at=time.time(),
                replication_factor=replication_factor
            )
            
            self.files[path] = file_info
            
            # Update parent directory
            if parent_path in self.directories:
                self.directories[parent_path].children.add(path)
                self.directories[parent_path].modified_at = time.time()
            
            self._persist_metadata()
            logger.info(f"Created file: {path}")
            return file_info
    
    def get_file(self, path: str) -> Optional[FileInfo]:
        """Get file metadata."""
        with self.lock:
            return self.files.get(path)
    
    def delete_file(self, path: str) -> List[str]:
        """Delete a file and return chunk IDs to be deleted."""
        with self.lock:
            if path not in self.files:
                raise FileNotFoundError(f"File not found: {path}")
            
            file_info = self.files[path]
            chunk_ids = file_info.chunks.copy()
            
            # Remove file
            del self.files[path]
            
            # Update parent directory
            parent_path = os.path.dirname(path)
            if parent_path in self.directories:
                self.directories[parent_path].children.discard(path)
                self.directories[parent_path].modified_at = time.time()
            
            # Remove chunk metadata
            for chunk_id in chunk_ids:
                if chunk_id in self.chunks:
                    del self.chunks[chunk_id]
            
            self._persist_metadata()
            logger.info(f"Deleted file: {path}")
            return chunk_ids
    
    def create_directory(self, path: str):
        """Create a new directory."""
        with self.lock:
            if path in self.directories:
                raise FileExistsError(f"Directory already exists: {path}")
            
            # Ensure parent directory exists
            parent_path = os.path.dirname(path)
            if parent_path != '/' and parent_path not in self.directories:
                raise FileNotFoundError(f"Parent directory not found: {parent_path}")
            
            # Create directory
            self.directories[path] = Directory(
                path=path,
                created_at=time.time(),
                modified_at=time.time(),
                children=set()
            )
            
            # Update parent directory
            if parent_path in self.directories:
                self.directories[parent_path].children.add(path)
                self.directories[parent_path].modified_at = time.time()
            
            self._persist_metadata()
            logger.info(f"Created directory: {path}")
    
    def list_directory(self, path: str) -> List[Dict]:
        """List contents of a directory."""
        with self.lock:
            if path not in self.directories:
                raise FileNotFoundError(f"Directory not found: {path}")
            
            directory = self.directories[path]
            contents = []
            
            for child_path in directory.children:
                if child_path in self.files:
                    file_info = self.files[child_path]
                    contents.append({
                        'type': 'file',
                        'path': child_path,
                        'name': os.path.basename(child_path),
                        'size': file_info.size,
                        'created_at': file_info.created_at,
                        'modified_at': file_info.modified_at
                    })
                elif child_path in self.directories:
                    dir_info = self.directories[child_path]
                    contents.append({
                        'type': 'directory',
                        'path': child_path,
                        'name': os.path.basename(child_path),
                        'created_at': dir_info.created_at,
                        'modified_at': dir_info.modified_at
                    })
            
            return sorted(contents, key=lambda x: x['name'])
    
    def add_chunk(self, file_path: str, chunk_info: ChunkInfo):
        """Add a chunk to a file."""
        with self.lock:
            if file_path not in self.files:
                raise FileNotFoundError(f"File not found: {file_path}")
            
            self.files[file_path].chunks.append(chunk_info.chunk_id)
            self.files[file_path].modified_at = time.time()
            self.chunks[chunk_info.chunk_id] = chunk_info
            
            self._persist_metadata()
    
    def get_chunk(self, chunk_id: str) -> Optional[ChunkInfo]:
        """Get chunk metadata."""
        with self.lock:
            return self.chunks.get(chunk_id)
    
    def update_chunk_replicas(self, chunk_id: str, replicas: List[str]):
        """Update chunk replica locations."""
        with self.lock:
            if chunk_id in self.chunks:
                self.chunks[chunk_id].replicas = replicas
                self._persist_metadata()
    
    def _persist_metadata(self):
        """Persist metadata to disk."""
        try:
            os.makedirs(self.persistence_path, exist_ok=True)
            
            # Save files
            files_data = {path: asdict(info) for path, info in self.files.items()}
            with open(os.path.join(self.persistence_path, 'files.json'), 'w') as f:
                json.dump(files_data, f, indent=2)
            
            # Save directories
            dirs_data = {}
            for path, dir_info in self.directories.items():
                dirs_data[path] = {
                    'path': dir_info.path,
                    'created_at': dir_info.created_at,
                    'modified_at': dir_info.modified_at,
                    'children': list(dir_info.children)
                }
            with open(os.path.join(self.persistence_path, 'directories.json'), 'w') as f:
                json.dump(dirs_data, f, indent=2)
            
            # Save chunks
            chunks_data = {chunk_id: asdict(info) for chunk_id, info in self.chunks.items()}
            with open(os.path.join(self.persistence_path, 'chunks.json'), 'w') as f:
                json.dump(chunks_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to persist metadata: {e}")
    
    def _load_metadata(self):
        """Load metadata from disk."""
        try:
            # Load files
            files_path = os.path.join(self.persistence_path, 'files.json')
            if os.path.exists(files_path):
                with open(files_path, 'r') as f:
                    files_data = json.load(f)
                    for path, data in files_data.items():
                        self.files[path] = FileInfo(**data)
            
            # Load directories
            dirs_path = os.path.join(self.persistence_path, 'directories.json')
            if os.path.exists(dirs_path):
                with open(dirs_path, 'r') as f:
                    dirs_data = json.load(f)
                    for path, data in dirs_data.items():
                        self.directories[path] = Directory(
                            path=data['path'],
                            created_at=data['created_at'],
                            modified_at=data['modified_at'],
                            children=set(data['children'])
                        )
            
            # Load chunks
            chunks_path = os.path.join(self.persistence_path, 'chunks.json')
            if os.path.exists(chunks_path):
                with open(chunks_path, 'r') as f:
                    chunks_data = json.load(f)
                    for chunk_id, data in chunks_data.items():
                        self.chunks[chunk_id] = ChunkInfo(**data)
            
            logger.info("Loaded metadata from disk")
            
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")