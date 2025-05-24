"""
Integration tests for file operations.
"""
import unittest
import tempfile
import shutil
import time
import threading
from namenode.server import NameNodeServer
from datanode.server import DataNodeServer
from client.api_client import DFSClient


class TestFileOperations(unittest.TestCase):
    """Integration tests for file operations."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test cluster."""
        # Start NameNode
        cls.namenode = NameNodeServer()
        cls.namenode_thread = threading.Thread(
            target=cls.namenode.start,
            kwargs={'host': 'localhost', 'port': 19870},
            daemon=True
        )
        cls.namenode_thread.start()
        time.sleep(2)  # Wait for NameNode to start
        
        # Start DataNodes
        cls.datanodes = []
        cls.datanode_threads = []
        
        for i in range(3):
            datanode = DataNodeServer(f'test-node-{i}')
            thread = threading.Thread(
                target=datanode.start,
                kwargs={'host': 'localhost', 'port': 18081 + i},
                daemon=True
            )
            thread.start()
            
            cls.datanodes.append(datanode)
            cls.datanode_threads.append(thread)
        
        time.sleep(2)  # Wait for DataNodes to start
        
        # Create client
        cls.client = DFSClient('localhost', 18080)
    
    @classmethod
    def tearDownClass(cls):
        """Stop test cluster."""
        cls.namenode.stop()
        for datanode in cls.datanodes:
            datanode.stop()
    
    def test_upload_download_file(self):
        """Test uploading and downloading a file."""
        # Create test file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        test_data = b'Test file content' * 1000
        temp_file.write(test_data)
        temp_file.close()
        
        try:
            # Upload file
            dfs_path = '/test/upload.txt'
            self.client.create_directory('/test')
            self.client.upload_file(temp_file.name, dfs_path)
            
            # Download file
            download_path = tempfile.mktemp()
            self.client.download_file(dfs_path, download_path)
            
            # Verify content
            with open(download_path, 'rb') as f:
                downloaded_data = f.read()
            
            self.assertEqual(test_data, downloaded_data)
            
            # Clean up
            os.unlink(download_path)
            
        finally:
            os.unlink(temp_file.name)
    
    def test_file_operations(self):
        """Test various file operations."""
        # Create directory
        self.client.create_directory('/testdir')
        
        # Create files
        self.client.create_file('/testdir/file1.txt')
        self.client.create_file('/testdir/file2.txt')
        
        # List directory
        contents = self.client.list_directory('/testdir')
        self.assertEqual(len(contents), 2)
        
        # Get file info
        info = self.client.get_file_info('/testdir/file1.txt')
        self.assertIsNotNone(info)
        self.assertEqual(info['path'], '/testdir/file1.txt')
        
        # Delete file
        self.client.delete_file('/testdir/file1.txt')
        
        # Verify deletion
        contents = self.client.list_directory('/testdir')
        self.assertEqual(len(contents), 1)
    
    def test_cluster_stats(self):
        """Test cluster statistics."""
        stats = self.client.get_cluster_stats()
        
        self.assertIn('total_nodes', stats)
        self.assertIn('alive_nodes', stats)
        self.assertIn('total_space', stats)
        self.assertIn('used_space', stats)
        
        # Should have 3 nodes
        self.assertEqual(stats['total_nodes'], 3)
        self.assertEqual(stats['alive_nodes'], 3)


if __name__ == '__main__':
    unittest.main()