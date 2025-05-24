#!/bin/bash
# Demo script for the Distributed File System

echo "=== Distributed File System Demo ==="
echo ""
echo "This demo will showcase the main features of the DFS."
echo "Press Enter to continue..."
read

# 1. Show cluster status
echo ""
echo "1. CLUSTER STATUS"
echo "================="
python3 scripts/healthcheck.py
echo ""
echo "Press Enter to continue..."
read

# 2. Create directory structure
echo ""
echo "2. CREATING DIRECTORY STRUCTURE"
echo "==============================="
echo "Creating directories..."
docker-compose exec -T client python -m client.cli mkdir /demo
docker-compose exec -T client python -m client.cli mkdir /demo/documents
docker-compose exec -T client python -m client.cli mkdir /demo/images
docker-compose exec -T client python -m client.cli mkdir /demo/videos
echo ""
echo "Listing root directory:"
docker-compose exec -T client python -m client.cli ls /
echo ""
echo "Press Enter to continue..."
read

# 3. Create and upload files
echo ""
echo "3. FILE UPLOAD DEMONSTRATION"
echo "============================"
echo "Creating sample files..."
docker-compose exec -T client bash -c "echo 'This is a demo document for the distributed file system.' > /workspace/demo_doc.txt"
docker-compose exec -T client bash -c "echo 'Another document with important information.' > /workspace/demo_doc2.txt"
docker-compose exec -T client bash -c "dd if=/dev/urandom of=/workspace/demo_image.jpg bs=1M count=2 2>/dev/null"
docker-compose exec -T client bash -c "dd if=/dev/urandom of=/workspace/demo_video.mp4 bs=1M count=10 2>/dev/null"

echo ""
echo "Uploading files to DFS..."
docker-compose exec -T client python -m client.cli upload /workspace/demo_doc.txt /demo/documents/readme.txt
docker-compose exec -T client python -m client.cli upload /workspace/demo_doc2.txt /demo/documents/notes.txt
docker-compose exec -T client python -m client.cli upload /workspace/demo_image.jpg /demo/images/photo.jpg
docker-compose exec -T client python -m client.cli upload /workspace/demo_video.mp4 /demo/videos/movie.mp4

echo ""
echo "Listing uploaded files:"
docker-compose exec -T client python -m client.cli ls /demo/documents
docker-compose exec -T client python -m client.cli ls /demo/images
docker-compose exec -T client python -m client.cli ls /demo/videos
echo ""
echo "Press Enter to continue..."
read

# 4. Show file information
echo ""
echo "4. FILE INFORMATION"
echo "==================="
echo "Getting detailed info about a large file:"
docker-compose exec -T client python -m client.cli info /demo/videos/movie.mp4
echo ""
echo "Press Enter to continue..."
read

# 5. Download files
echo ""
echo "5. FILE DOWNLOAD DEMONSTRATION"
echo "=============================="
echo "Downloading a file from DFS..."
docker-compose exec -T client python -m client.cli download /demo/documents/readme.txt /workspace/downloaded_readme.txt
echo ""
echo "Content of downloaded file:"
docker-compose exec -T client cat /workspace/downloaded_readme.txt
echo ""
echo "Press Enter to continue..."
read

# 6. Show cluster statistics
echo ""
echo "6. CLUSTER STATISTICS"
echo "===================="
docker-compose exec -T client python -m client.cli stats
echo ""
echo "Press Enter to continue..."
read

# 7. Demonstrate replication
echo ""
echo "7. REPLICATION DEMONSTRATION"
echo "==========================="
echo "Files are automatically replicated across nodes."
echo "Let's check where our chunks are stored..."
echo ""
curl -s http://localhost:8080/chunks/status | python3 -m json.tool | head -20
echo ""
echo "Press Enter to continue..."
read

# 8. Web UI
echo ""
echo "8. WEB USER INTERFACE"
echo "===================="
echo "The system also provides a modern web interface."
echo ""
echo "Open your browser and visit:"
echo "• File Explorer: http://localhost:3001"
echo "• Monitoring Dashboard: http://localhost:3000 (admin/admin)"
echo ""
echo "Press Enter to continue..."
read

# 9. Cleanup demo files
echo ""
echo "9. CLEANUP (OPTIONAL)"
echo "===================="
echo "Do you want to clean up the demo files? (y/n)"
read -n 1 cleanup
echo ""

if [[ $cleanup == "y" || $cleanup == "Y" ]]; then
    echo "Cleaning up demo files..."
    docker-compose exec -T client python -m client.cli rm /demo/documents/readme.txt
    docker-compose exec -T client python -m client.cli rm /demo/documents/notes.txt
    docker-compose exec -T client python -m client.cli rm /demo/images/photo.jpg
    docker-compose exec -T client python -m client.cli rm /demo/videos/movie.mp4
    echo "Demo files cleaned up."
else
    echo "Demo files kept in the system."
fi

echo ""
echo "=== Demo Complete ==="
echo ""
echo "You've seen the main features of the Distributed File System:"
echo "✓ Cluster management and monitoring"
echo "✓ Directory creation and navigation"
echo "✓ File upload with automatic chunking"
echo "✓ File replication across nodes"
echo "✓ File download and retrieval"
echo "✓ Web-based user interface"
echo ""
echo "For more information, check the README.md file."