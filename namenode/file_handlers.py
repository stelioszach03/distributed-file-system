"""
File upload and download handlers for NameNode API.
"""
import io
import json
from flask import request, Response, send_file
from werkzeug.exceptions import BadRequest, NotFound
from common.constants import CHUNK_SIZE, DATANODE_API_PORT
from common.utils import setup_logger, calculate_checksum
import requests
import uuid

logger = setup_logger('FileHandlers')


class FileHandlers:
    """Handles file upload and download operations."""
    
    def __init__(self, metadata_manager, chunk_manager):
        self.metadata_manager = metadata_manager
        self.chunk_manager = chunk_manager
    
    def handle_file_upload(self, file_path: str):
        """Handle multipart file upload."""
        try:
            if 'file' not in request.files:
                raise BadRequest("No file part in request")
            
            file = request.files['file']
            if file.filename == '':
                raise BadRequest("No file selected")
            
            # Create file entry
            replication_factor = request.form.get('replication_factor', 3, type=int)
            file_info = self.metadata_manager.create_file(
                path=file_path,
                replication_factor=replication_factor
            )
            
            # Process file in chunks
            file_size = 0
            chunk_index = 0
            
            while True:
                chunk_data = file.read(CHUNK_SIZE)
                if not chunk_data:
                    break
                
                # Allocate chunk
                chunk_id, locations = self.chunk_manager.allocate_chunk(
                    len(chunk_data), 
                    replication_factor
                )
                
                # Upload to primary DataNode
                if locations:
                    success = self._upload_chunk_to_datanode(
                        chunk_id, 
                        chunk_data, 
                        locations[0]
                    )
                    
                    if success:
                        # Add chunk to file metadata
                        checksum = calculate_checksum(chunk_data)
                        chunk_info = {
                            'chunk_id': chunk_id,
                            'size': len(chunk_data),
                            'checksum': checksum,
                            'replicas': locations
                        }
                        
                        self.metadata_manager.add_chunk(file_path, chunk_info)
                        
                        # Trigger replication to other nodes
                        if len(locations) > 1:
                            self._trigger_replication(chunk_id, locations[0], locations[1:])
                
                file_size += len(chunk_data)
                chunk_index += 1
                
                # Report progress
                logger.info(f"Uploaded chunk {chunk_index} of {file_path}")
            
            # Update file size
            self.metadata_manager.update_file_size(file_path, file_size)
            
            return {
                'path': file_path,
                'size': file_size,
                'chunks': chunk_index,
                'message': 'File uploaded successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            # Clean up on failure
            try:
                self.metadata_manager.delete_file(file_path)
            except:
                pass
            raise
    
    def handle_file_download(self, file_path: str):
        """Handle file download by streaming chunks."""
        try:
            file_info = self.metadata_manager.get_file(file_path)
            if not file_info:
                raise NotFound(f"File not found: {file_path}")
            
            def generate():
                """Generator to stream file chunks."""
                for chunk_id in file_info.chunks:
                    chunk_info = self.metadata_manager.get_chunk(chunk_id)
                    if not chunk_info:
                        logger.error(f"Chunk {chunk_id} metadata not found")
                        continue
                    
                    # Try to download from available replicas
                    chunk_data = None
                    for node_id in chunk_info.replicas:
                        chunk_data = self._download_chunk_from_datanode(chunk_id, node_id)
                        if chunk_data:
                            break
                    
                    if chunk_data:
                        yield chunk_data
                    else:
                        logger.error(f"Failed to download chunk {chunk_id}")
                        raise Exception(f"Failed to download chunk {chunk_id}")
            
            # Return as streaming response
            response = Response(generate(), mimetype='application/octet-stream')
            response.headers['Content-Disposition'] = f'attachment; filename="{file_info.path.split("/")[-1]}"'
            response.headers['Content-Length'] = str(file_info.size)
            return response
            
        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {e}")
            raise
    
    def handle_chunk_status(self):
        """Get chunk distribution status."""
        try:
            chunks = {}
            for chunk_id, chunk_info in self.metadata_manager.chunks.items():
                locations = self.chunk_manager.get_chunk_locations(chunk_id)
                chunks[chunk_id] = {
                    'size': chunk_info.size,
                    'checksum': chunk_info.checksum,
                    'replicas': locations,
                    'health': 'healthy' if len(locations) >= chunk_info.replication_factor else 'degraded'
                }
            
            return {
                'total_chunks': len(chunks),
                'healthy_chunks': sum(1 for c in chunks.values() if c['health'] == 'healthy'),
                'degraded_chunks': sum(1 for c in chunks.values() if c['health'] == 'degraded'),
                'chunks': chunks
            }
        except Exception as e:
            logger.error(f"Failed to get chunk status: {e}")
            raise
    
    def _upload_chunk_to_datanode(self, chunk_id: str, data: bytes, node_id: str) -> bool:
        """Upload chunk to a specific DataNode."""
        try:
            node_info = self.chunk_manager.datanodes.get(node_id)
            if not node_info:
                logger.error(f"DataNode {node_id} not found")
                return False
            
            # Determine DataNode API port based on node_id
            port_offset = int(node_id.split('-')[-1]) - 1
            api_port = DATANODE_API_PORT + port_offset
            
            url = f"http://{node_info.host}:{api_port}/chunks/{chunk_id}"
            response = requests.put(
                url,
                data=data,
                headers={'Content-Type': 'application/octet-stream'},
                timeout=30
            )
            
            if response.status_code == 200:
                # Report successful storage
                self.chunk_manager.report_chunk_stored(chunk_id, node_id)
                return True
            else:
                logger.error(f"Failed to upload chunk {chunk_id} to {node_id}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading chunk {chunk_id} to {node_id}: {e}")
            return False
    
    def _download_chunk_from_datanode(self, chunk_id: str, node_id: str) -> bytes:
        """Download chunk from a specific DataNode."""
        try:
            node_info = self.chunk_manager.datanodes.get(node_id)
            if not node_info:
                logger.error(f"DataNode {node_id} not found")
                return None
            
            # Determine DataNode API port
            port_offset = int(node_id.split('-')[-1]) - 1
            api_port = DATANODE_API_PORT + port_offset
            
            url = f"http://{node_info.host}:{api_port}/chunks/{chunk_id}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Failed to download chunk {chunk_id} from {node_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading chunk {chunk_id} from {node_id}: {e}")
            return None
    
    def _trigger_replication(self, chunk_id: str, source_node: str, target_nodes: list):
        """Trigger chunk replication from source to target nodes."""
        try:
            node_info = self.chunk_manager.datanodes.get(source_node)
            if not node_info:
                return
            
            port_offset = int(source_node.split('-')[-1]) - 1
            api_port = DATANODE_API_PORT + port_offset
            
            url = f"http://{node_info.host}:{api_port}/replicate"
            
            # Prepare target node information
            targets = []
            for target_id in target_nodes:
                target_info = self.chunk_manager.datanodes.get(target_id)
                if target_info:
                    target_port_offset = int(target_id.split('-')[-1]) - 1
                    targets.append({
                        'node_id': target_id,
                        'host': target_info.host,
                        'api_port': DATANODE_API_PORT + target_port_offset
                    })
            
            response = requests.post(
                url,
                json={
                    'chunk_id': chunk_id,
                    'target_nodes': targets
                }
            )
            
            if response.status_code == 200:
                logger.info(f"Triggered replication of chunk {chunk_id} from {source_node} to {target_nodes}")
            
        except Exception as e:
            logger.error(f"Failed to trigger replication: {e}")