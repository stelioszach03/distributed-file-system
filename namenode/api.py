"""
REST API for the NameNode.
"""
from flask import Flask, jsonify, request, Response
from werkzeug.exceptions import BadRequest
import json
from common.constants import NAMENODE_API_PORT, CHUNK_SIZE
from common.messages import ChunkInfo
from common.utils import setup_logger, calculate_checksum


logger = setup_logger('NameNodeAPI')


class NameNodeAPI:
    """REST API for NameNode operations."""
    
    def __init__(self, metadata_manager, chunk_manager):
        self.app = Flask(__name__)
        self.metadata_manager = metadata_manager
        self.chunk_manager = chunk_manager
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register API routes."""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint."""
            return jsonify({'status': 'healthy'})
        
        @self.app.route('/datanodes/register', methods=['POST'])
        def register_datanode():
            """Register a new DataNode."""
            try:
                data = request.json
                node_id = data.get('node_id')
                host = data.get('host')
                port = data.get('port')
                
                if not all([node_id, host, port]):
                    raise BadRequest("node_id, host, and port are required")
                
                self.chunk_manager.register_datanode(node_id, host, port)
                
                return jsonify({
                    'status': 'registered',
                    'node_id': node_id
                }), 200
                
            except Exception as e:
                logger.error(f"Error registering DataNode: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/files', methods=['POST'])
        def create_file():
            """Create a new file."""
            try:
                data = request.json
                path = data.get('path')
                if not path:
                    raise BadRequest("Path is required")
                
                file_info = self.metadata_manager.create_file(
                    path=path,
                    replication_factor=data.get('replication_factor', 3)
                )
                
                return jsonify({
                    'path': file_info.path,
                    'created_at': file_info.created_at,
                    'replication_factor': file_info.replication_factor
                }), 201
                
            except FileExistsError as e:
                return jsonify({'error': str(e)}), 409
            except Exception as e:
                logger.error(f"Error creating file: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/files/<path:file_path>', methods=['GET'])
        def get_file(file_path):
            """Get file metadata."""
            file_path = '/' + file_path
            file_info = self.metadata_manager.get_file(file_path)
            
            if not file_info:
                return jsonify({'error': 'File not found'}), 404
            
            # Get chunk locations
            chunks_with_locations = []
            for chunk_id in file_info.chunks:
                chunk_info = self.metadata_manager.get_chunk(chunk_id)
                if chunk_info:
                    locations = self.chunk_manager.get_chunk_locations(chunk_id)
                    chunks_with_locations.append({
                        'chunk_id': chunk_id,
                        'size': chunk_info.size,
                        'checksum': chunk_info.checksum,
                        'locations': locations
                    })
            
            return jsonify({
                'path': file_info.path,
                'size': file_info.size,
                'chunks': chunks_with_locations,
                'created_at': file_info.created_at,
                'modified_at': file_info.modified_at,
                'replication_factor': file_info.replication_factor
            })
        
        @self.app.route('/files/<path:file_path>', methods=['DELETE'])
        def delete_file(file_path):
            """Delete a file."""
            try:
                file_path = '/' + file_path
                chunk_ids = self.metadata_manager.delete_file(file_path)
                
                # TODO: Trigger chunk deletion on DataNodes
                
                return jsonify({
                    'message': 'File deleted',
                    'chunks_to_delete': chunk_ids
                }), 200
                
            except FileNotFoundError as e:
                return jsonify({'error': str(e)}), 404
            except Exception as e:
                logger.error(f"Error deleting file: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/directories', methods=['POST'])
        def create_directory():
            """Create a new directory."""
            try:
                data = request.json
                path = data.get('path')
                if not path:
                    raise BadRequest("Path is required")
                
                self.metadata_manager.create_directory(path)
                return jsonify({'message': 'Directory created'}), 201
                
            except FileExistsError as e:
                return jsonify({'error': str(e)}), 409
            except Exception as e:
                logger.error(f"Error creating directory: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/directories/<path:dir_path>', methods=['GET'])
        @self.app.route('/directories/', methods=['GET'])
        def list_directory(dir_path=''):
            """List directory contents."""
            try:
                dir_path = '/' + dir_path if dir_path else '/'
                contents = self.metadata_manager.list_directory(dir_path)
                return jsonify({'contents': contents})
                
            except FileNotFoundError as e:
                return jsonify({'error': str(e)}), 404
            except Exception as e:
                logger.error(f"Error listing directory: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/chunks/allocate', methods=['POST'])
        def allocate_chunk():
            """Allocate a new chunk."""
            try:
                data = request.json
                size = data.get('size', CHUNK_SIZE)
                replication_factor = data.get('replication_factor', 3)
                
                chunk_id, locations = self.chunk_manager.allocate_chunk(size, replication_factor)
                
                return jsonify({
                    'chunk_id': chunk_id,
                    'locations': locations,
                    'size': size
                }), 200
                
            except Exception as e:
                logger.error(f"Error allocating chunk: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/chunks/<chunk_id>/complete', methods=['POST'])
        def complete_chunk(chunk_id):
            """Mark chunk upload as complete."""
            try:
                data = request.json
                file_path = data.get('file_path')
                size = data.get('size')
                checksum = data.get('checksum')
                
                if not all([file_path, size, checksum]):
                    raise BadRequest("file_path, size, and checksum are required")
                
                # Create chunk info
                chunk_info = ChunkInfo(
                    chunk_id=chunk_id,
                    size=size,
                    checksum=checksum,
                    replicas=[]
                )
                
                # Add chunk to file
                self.metadata_manager.add_chunk(file_path, chunk_info)
                
                return jsonify({'message': 'Chunk added to file'}), 200
                
            except Exception as e:
                logger.error(f"Error completing chunk: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/cluster/stats', methods=['GET'])
        def cluster_stats():
            """Get cluster statistics."""
            stats = self.chunk_manager.get_cluster_stats()
            return jsonify(stats)
        
        @self.app.route('/datanodes', methods=['GET'])
        def list_datanodes():
            """List all DataNodes."""
            datanodes = []
            for node_id, node_info in self.chunk_manager.datanodes.items():
                datanodes.append({
                    'node_id': node_id,
                    'host': node_info.host,
                    'port': node_info.port,
                    'available_space': node_info.available_space,
                    'used_space': node_info.used_space,
                    'chunk_count': node_info.chunk_count,
                    'is_alive': node_info.is_alive,
                    'last_heartbeat': node_info.last_heartbeat
                })
            return jsonify({'datanodes': datanodes})
    
    def run(self, host='0.0.0.0', port=NAMENODE_API_PORT):
        """Run the API server."""
        logger.info(f"Starting NameNode API on {host}:{port}")
        self.app.run(host=host, port=port, threaded=True)