"""
Unit tests for NameNode components.
"""
import unittest
import tempfile
import shutil
from namenode.metadata_manager import MetadataManager
from namenode.chunk_manager import ChunkManager
from common.messages import ChunkInfo, FileInfo


class TestMetadataManager(unittest.TestCase):
    """Test cases for MetadataManager."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.metadata_manager = MetadataManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_create_file(self):
        """Test file creation."""
        file_info = self.metadata_manager.create_file('/test.txt', size=100)
        
        self.assertEqual(file_info.path, '/test.txt')
        self.assertEqual(file_info.size, 100)
        self.assertEqual(len(file_info.chunks), 0)
    
    def test_create_duplicate_file(self):
        """Test creating duplicate file raises error."""
        self.metadata_manager.create_file('/test.txt')
        
        with self.assertRaises(FileExistsError):
            self.metadata_manager.create_file('/test.txt')
    
    def test_get_file(self):
        """Test file retrieval."""
        self.metadata_manager.create_file('/test.txt', size=100)
        file_info = self.metadata_manager.get_file('/test.txt')
        
        self.assertIsNotNone(file_info)
        self.assertEqual(file_info.path, '/test.txt')
    
    def test_delete_file(self):
        """Test file deletion."""
        self.metadata_manager.create_file('/test.txt')
        chunk_ids = self.metadata_manager.delete_file('/test.txt')
        
        self.assertEqual(len(chunk_ids), 0)
        self.assertIsNone(self.metadata_manager.get_file('/test.txt'))
    
    def test_create_directory(self):
        """Test directory creation."""
        self.metadata_manager.create_directory('/testdir')
        contents = self.metadata_manager.list_directory('/testdir')
        
        self.assertEqual(len(contents), 0)
    
    def test_list_directory(self):
        """Test directory listing."""
        self.metadata_manager.create_directory('/testdir')
        self.metadata_manager.create_file('/testdir/file1.txt')
        self.metadata_manager.create_file('/testdir/file2.txt')
        self.metadata_manager.create_directory('/testdir/subdir')
        
        contents = self.metadata_manager.list_directory('/testdir')
        
        self.assertEqual(len(contents), 3)
        names = [item['name'] for item in contents]
        self.assertIn('file1.txt', names)
        self.assertIn('file2.txt', names)
        self.assertIn('subdir', names)
    
    def test_add_chunk(self):
        """Test adding chunk to file."""
        self.metadata_manager.create_file('/test.txt')
        
        chunk_info = ChunkInfo(
            chunk_id='chunk-123',
            size=1024,
            checksum='abc123',
            replicas=['node1', 'node2']
        )
        
        self.metadata_manager.add_chunk('/test.txt', chunk_info)
        
        file_info = self.metadata_manager.get_file('/test.txt')
        self.assertEqual(len(file_info.chunks), 1)
        self.assertEqual(file_info.chunks[0], 'chunk-123')


class TestChunkManager(unittest.TestCase):
    """Test cases for ChunkManager."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        metadata_manager = MetadataManager(self.temp_dir)
        self.chunk_manager = ChunkManager(metadata_manager)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_register_datanode(self):
        """Test DataNode registration."""
        node_info = self.chunk_manager.register_datanode('node1', 'localhost', 9866)
        
        self.assertEqual(node_info.node_id, 'node1')
        self.assertEqual(node_info.host, 'localhost')
        self.assertEqual(node_info.port, 9866)
    
    def test_allocate_chunk_no_nodes(self):
        """Test chunk allocation with no available nodes."""
        chunk_id, locations = self.chunk_manager.allocate_chunk(1024)
        
        self.assertIsNotNone(chunk_id)
        self.assertEqual(len(locations), 0)
    
    def test_allocate_chunk_with_nodes(self):
        """Test chunk allocation with available nodes."""
        # Register nodes
        self.chunk_manager.register_datanode('node1', 'localhost', 9866)
        self.chunk_manager.register_datanode('node2', 'localhost', 9867)
        self.chunk_manager.register_datanode('node3', 'localhost', 9868)
        
        # Update node info
        self.chunk_manager.update_datanode_info('node1', 1000000, 0, 0)
        self.chunk_manager.update_datanode_info('node2', 2000000, 0, 0)
        self.chunk_manager.update_datanode_info('node3', 3000000, 0, 0)
        
        # Allocate chunk
        chunk_id, locations = self.chunk_manager.allocate_chunk(1024, replication_factor=2)
        
        self.assertIsNotNone(chunk_id)
        self.assertEqual(len(locations), 2)
        # Should select nodes with most available space
        self.assertIn('node3', locations)
        self.assertIn('node2', locations)
    
    def test_handle_datanode_failure(self):
        """Test handling DataNode failure."""
        # Register node and add chunks
        self.chunk_manager.register_datanode('node1', 'localhost', 9866)
        chunk_id, _ = self.chunk_manager.allocate_chunk(1024)
        
        # Simulate failure
        self.chunk_manager.handle_datanode_failure('node1')
        
        node_info = self.chunk_manager.datanodes['node1']
        self.assertFalse(node_info.is_alive)


if __name__ == '__main__':
    unittest.main()