"""
Main DataNode server implementation.
"""
import os  # Add this import
import socket
import threading
import time
import uuid
import requests
from flask import Flask, jsonify, request, Response
from prometheus_client import start_http_server
from common.constants import (
    NAMENODE_HOST, NAMENODE_PORT, DATANODE_PORT, DATANODE_API_PORT,
    HEARTBEAT_INTERVAL, METRICS_PORT
)
from common.messages import Message, MessageType, HeartbeatMessage
from common.utils import setup_logger
from .storage_manager import StorageManager
from .replication_manager import ReplicationManager
from .health_reporter import HealthReporter


logger = setup_logger('DataNode')


class DataNodeServer:
    """Main DataNode server handling storage and replication."""
    
    def __init__(self, node_id: str = None):
        self.node_id = node_id or str(uuid.uuid4())
        self.storage_manager = StorageManager(self.node_id)
        self.replication_manager = ReplicationManager(self.storage_manager, self.node_id)
        self.health_reporter = HealthReporter(self.storage_manager)
        
        self.app = Flask(__name__)
        self.running = False
        self.namenode_host = NAMENODE_HOST
        self.namenode_port = NAMENODE_PORT
        
        # Register with NameNode
        self._register_with_namenode()
        
        # Setup API routes
        self._setup_routes()
        
        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
    
    def _register_with_namenode(self):
        """Register this DataNode with the NameNode."""
        try:
            # Get hostname
            hostname = socket.gethostname()
            
            # Send registration request
            url = f"http://{self.namenode_host}:8080/datanodes/register"
            data = {
                'node_id': self.node_id,
                'host': hostname,
                'port': DATANODE_PORT
            }
            
            response = requests.post(url, json=data, timeout=5)
            if response.status_code == 200:
                logger.info(f"Registered with NameNode as {self.node_id}")
            else:
                logger.error(f"Failed to register with NameNode: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to register with NameNode: {e}")
    
    def _setup_routes(self):
        """Setup Flask API routes."""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint."""
            health_data = self.health_reporter.get_health_status()
            return jsonify(health_data)
        
        @self.app.route('/chunks/<chunk_id>', methods=['PUT'])
        def store_chunk(chunk_id):
            """Store a chunk."""
            try:
                start_time = time.time()
                data = request.get_data()
                
                # Store chunk
                checksum = self.storage_manager.store_chunk(chunk_id, data)
                
                # Record metrics
                duration = time.time() - start_time
                self.health_reporter.record_operation('store', duration)
                
                return jsonify({
                    'chunk_id': chunk_id,
                    'size': len(data),
                    'checksum': checksum
                }), 200
                
            except Exception as e:
                logger.error(f"Failed to store chunk {chunk_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/chunks/<chunk_id>', methods=['GET'])
        def retrieve_chunk(chunk_id):
            """Retrieve a chunk."""
            try:
                start_time = time.time()
                data = self.storage_manager.retrieve_chunk(chunk_id)
                
                if data is None:
                    return jsonify({'error': 'Chunk not found'}), 404
                
                # Record metrics
                duration = time.time() - start_time
                self.health_reporter.record_operation('retrieve', duration)
                
                return Response(data, mimetype='application/octet-stream')
                
            except Exception as e:
                logger.error(f"Failed to retrieve chunk {chunk_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/chunks/<chunk_id>', methods=['DELETE'])
        def delete_chunk(chunk_id):
            """Delete a chunk."""
            try:
                start_time = time.time()
                success = self.storage_manager.delete_chunk(chunk_id)
                
                if not success:
                    return jsonify({'error': 'Chunk not found'}), 404
                
                # Record metrics
                duration = time.time() - start_time
                self.health_reporter.record_operation('delete', duration)
                
                return jsonify({'message': 'Chunk deleted'}), 200
                
            except Exception as e:
                logger.error(f"Failed to delete chunk {chunk_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/chunks/<chunk_id>/exists', methods=['GET'])
        def check_chunk_exists(chunk_id):
            """Check if chunk exists."""
            chunk_path = self.storage_manager._get_chunk_path(chunk_id)
            if os.path.exists(chunk_path):
                return '', 200
            return '', 404
        
        @self.app.route('/replicate', methods=['POST'])
        def replicate_chunk():
            """Replicate a chunk to other nodes."""
            try:
                data = request.json
                chunk_id = data.get('chunk_id')
                target_nodes = data.get('target_nodes', [])
                
                if not chunk_id:
                    return jsonify({'error': 'chunk_id required'}), 400
                
                # Queue replication
                self.replication_manager.replicate_chunk(chunk_id, target_nodes)
                
                return jsonify({'message': 'Replication queued'}), 200
                
            except Exception as e:
                logger.error(f"Failed to queue replication: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/chunks', methods=['GET'])
        def list_chunks():
            """List all stored chunks."""
            chunks = self.storage_manager.list_chunks()
            return jsonify({'chunks': chunks, 'count': len(chunks)})
    
    def _heartbeat_loop(self):
        """Send periodic heartbeats to NameNode."""
        while True:
            try:
                time.sleep(HEARTBEAT_INTERVAL)
                
                # Get health status
                health = self.health_reporter.get_health_status()
                
                # Create heartbeat message
                heartbeat = HeartbeatMessage(
                    node_id=self.node_id,
                    available_space=health['storage']['available'],
                    used_space=health['storage']['used'],
                    chunk_count=health['storage']['chunk_count'],
                    cpu_usage=health['system']['cpu_usage'],
                    memory_usage=health['system']['memory_usage'],
                    timestamp=time.time()
                )
                
                # Send heartbeat
                message = Message(
                    type=MessageType.HEARTBEAT,
                    payload=heartbeat.__dict__
                )
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.namenode_host, self.namenode_port))
                sock.send(message.to_json().encode('utf-8'))
                
                # Wait for acknowledgment
                response = sock.recv(1024).decode('utf-8')
                sock.close()
                
                logger.debug(f"Heartbeat sent, response: {response}")
                
            except Exception as e:
                logger.error(f"Failed to send heartbeat: {e}")
    
    def start(self, host='0.0.0.0', port=DATANODE_API_PORT):
        """Start the DataNode server."""
        try:
            self.running = True
            
            # Start Prometheus metrics server
            start_http_server(METRICS_PORT)
            logger.info(f"Metrics server started on port {METRICS_PORT}")
            
            # Start Flask API
            logger.info(f"DataNode {self.node_id} starting on {host}:{port}")
            self.app.run(host=host, port=port, threaded=True)
            
        except Exception as e:
            logger.error(f"Failed to start DataNode: {e}")
            raise
        finally:
            self.stop()
    
    def stop(self):
        """Stop the DataNode server."""
        logger.info(f"Stopping DataNode {self.node_id}...")
        self.running = False
        self.replication_manager.stop()


def main():
    """Main entry point."""
    import os
    node_id = os.environ.get('DATANODE_ID')
    server = DataNodeServer(node_id)
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down DataNode...")
        server.stop()


if __name__ == '__main__':
    main()