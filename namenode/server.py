"""
Main NameNode server implementation.
"""
import socket
import threading
import json
import time
from common.constants import NAMENODE_PORT, NAMENODE_API_PORT
from common.messages import Message, MessageType, HeartbeatMessage
from common.utils import setup_logger
from .metadata_manager import MetadataManager
from .chunk_manager import ChunkManager
from .heartbeat_monitor import HeartbeatMonitor
from .api import NameNodeAPI


logger = setup_logger('NameNode')


class NameNodeServer:
    """Main NameNode server handling metadata and chunk management."""
    
    def __init__(self):
        self.metadata_manager = MetadataManager()
        self.chunk_manager = ChunkManager(self.metadata_manager)
        self.heartbeat_monitor = HeartbeatMonitor(
            self.chunk_manager,
            self.chunk_manager.handle_datanode_failure
        )
        self.api = NameNodeAPI(self.metadata_manager, self.chunk_manager)
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = False
    
    def start(self, host='0.0.0.0', port=NAMENODE_PORT):
        """Start the NameNode server."""
        try:
            self.socket.bind((host, port))
            self.socket.listen(100)
            self.running = True
            
            logger.info(f"NameNode started on {host}:{port}")
            
            # Start API server in separate thread
            api_thread = threading.Thread(
                target=self.api.run,
                kwargs={'host': host, 'port': NAMENODE_API_PORT},
                daemon=True
            )
            api_thread.start()
            
            # Accept connections
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    logger.info(f"Connection from {address}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        logger.error(f"Error accepting connection: {e}")
        
        except Exception as e:
            logger.error(f"Failed to start NameNode: {e}")
            raise
        finally:
            self.stop()
    
    def _handle_client(self, client_socket: socket.socket, address):
        """Handle client connection."""
        try:
            # Receive initial message
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                return
            
            message = Message.from_json(data)
            
            if message.type == MessageType.HEARTBEAT:
                self._handle_heartbeat(message, client_socket)
            else:
                logger.warning(f"Unknown message type: {message.type}")
                
        except Exception as e:
            logger.error(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
    
    def _handle_heartbeat(self, message: Message, client_socket: socket.socket):
        """Handle heartbeat from DataNode."""
        try:
            heartbeat = HeartbeatMessage(**message.payload)
            
            # Update DataNode info
            self.chunk_manager.update_datanode_info(
                node_id=heartbeat.node_id,
                available_space=heartbeat.available_space,
                used_space=heartbeat.used_space,
                chunk_count=heartbeat.chunk_count
            )
            
            # Record heartbeat
            self.heartbeat_monitor.record_heartbeat(heartbeat.node_id)
            
            # Send acknowledgment
            ack_message = Message(
                type=MessageType.HEARTBEAT_ACK,
                payload={'status': 'ok', 'timestamp': time.time()}
            )
            client_socket.send(ack_message.to_json().encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}")
    
    def stop(self):
        """Stop the NameNode server."""
        logger.info("Stopping NameNode...")
        self.running = False
        self.heartbeat_monitor.stop()
        self.socket.close()


def main():
    """Main entry point."""
    server = NameNodeServer()
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down NameNode...")
        server.stop()


if __name__ == '__main__':
    main()