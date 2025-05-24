"""
Unit tests for DataNode components.
"""
import unittest
import tempfile
import shutil
import os
from datanode.storage_manager import StorageManager
from datanode.health_reporter import HealthReporter


class TestStorageManager(unittest.TestCase):
    """Test cases for StorageManager."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_manager = StorageManager('test-node', self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_store_chunk(self):
        """Test chunk storage."""
        chunk_id = 'test-chunk-123'
        data = b'Hello, World!' * 1000
        
        checksum = self.storage_manager.store_chunk(chunk_id, data)
        
        self.assertIsNotNone(checksum)
        chunk_path = os.path.join(self.temp_dir, f"{chunk_id}.chunk")
        self.assertTrue(os.path.exists(chunk_path))
    
    def test_retrieve_chunk(self):
        """Test chunk retrieval."""
        chunk_id = 'test-chunk-456'
        original_data = b'Test data for chunk'
        
        self.storage_manager.store_chunk(chunk_id, original_data)
        retrieved_data = self.storage_manager.retrieve_chunk(chunk_id)
        
        self.assertEqual(original_data, retrieved_data)
    
    def test_retrieve_nonexistent_chunk(self):
        """Test retrieving non-existent chunk."""
        data = self.storage_manager.retrieve_chunk('nonexistent')
        self.assertIsNone(data)
    
    def test_delete_chunk(self):
        """Test chunk deletion."""
        chunk_id = 'test-chunk-789'
        data = b'Data to delete'
        
        self.storage_manager.store_chunk(chunk_id, data)
        success = self.storage_manager.delete_chunk(chunk_id)
        
        self.assertTrue(success)
        chunk_path = os.path.join(self.temp_dir, f"{chunk_id}.chunk")
        self.assertFalse(os.path.exists(chunk_path))
    
    def test_list_chunks(self):
        """Test listing chunks."""
        # Store some chunks
        self.storage_manager.store_chunk('chunk1', b'data1')
        self.storage_manager.store_chunk('chunk2', b'data2')
        self.storage_manager.store_chunk('chunk3', b'data3')
        
        chunks = self.storage_manager.list_chunks()
        
        self.assertEqual(len(chunks), 3)
        self.assertIn('chunk1', chunks)
        self.assertIn('chunk2', chunks)
        self.assertIn('chunk3', chunks)
    
    def test_get_storage_stats(self):
        """Test storage statistics."""
        stats = self.storage_manager.get_storage_stats()
        
        self.assertIn('total_space', stats)
        self.assertIn('available_space', stats)
        self.assertIn('used_space', stats)
        self.assertIn('chunk_count', stats)
        self.assertGreaterEqual(stats['total_space'], 0)


class TestHealthReporter(unittest.TestCase):
    """Test cases for HealthReporter."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        storage_manager = StorageManager('test-node', self.temp_dir)
        self.health_reporter = HealthReporter(storage_manager)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_get_health_status(self):
        """Test health status reporting."""
        health = self.health_reporter.get_health_status()
        
        self.assertIn('node_id', health)
        self.assertIn('uptime', health)
        self.assertIn('storage', health)
        self.assertIn('system', health)
        self.assertIn('timestamp', health)
        
        # Check storage info
        self.assertIn('used', health['storage'])
        self.assertIn('available', health['storage'])
        self.assertIn('total', health['storage'])
        
        # Check system info
        self.assertIn('cpu_usage', health['system'])
        self.assertIn('memory_usage', health['system'])


if __name__ == '__main__':
    unittest.main()