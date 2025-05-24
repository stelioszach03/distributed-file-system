#!/bin/bash
# Script to test the distributed file system

echo "=== Testing Distributed File System ==="
echo ""

# Check if services are running
echo "1. Checking services..."
docker-compose ps

echo ""
echo "2. Checking cluster health..."
python3 scripts/healthcheck.py

echo ""
echo "3. Creating test files..."
docker-compose exec -T client bash -c "echo 'Test file 1' > /workspace/test1.txt"
docker-compose exec -T client bash -c "echo 'Test file 2 with more content for testing' > /workspace/test2.txt"
docker-compose exec -T client bash -c "dd if=/dev/urandom of=/workspace/test_large.dat bs=1M count=5 2>/dev/null"

echo ""
echo "4. Testing file upload..."
docker-compose exec -T client python -m client.cli upload /workspace/test1.txt /tests/test1.txt
docker-compose exec -T client python -m client.cli upload /workspace/test2.txt /tests/test2.txt
docker-compose exec -T client python -m client.cli upload /workspace/test_large.dat /tests/large.dat

echo ""
echo "5. Listing uploaded files..."
docker-compose exec -T client python -m client.cli ls /tests

echo ""
echo "6. Testing file download..."
docker-compose exec -T client python -m client.cli download /tests/test1.txt /workspace/downloaded_test1.txt
docker-compose exec -T client bash -c "cat /workspace/downloaded_test1.txt"

echo ""
echo "7. Getting file info..."
docker-compose exec -T client python -m client.cli info /tests/large.dat

echo ""
echo "8. Testing directory operations..."
docker-compose exec -T client python -m client.cli mkdir /tests/subdir
docker-compose exec -T client python -m client.cli ls /tests

echo ""
echo "9. Testing file deletion..."
docker-compose exec -T client python -m client.cli rm /tests/test2.txt

echo ""
echo "10. Final cluster statistics..."
docker-compose exec -T client python -m client.cli stats

echo ""
echo "=== Test Complete ==="
echo ""
echo "If all tests passed, the system is working correctly!"
echo ""
echo "Access points:"
echo "- Web UI: http://localhost:3001"
echo "- Grafana: http://localhost:3000 (admin/admin)"
echo "- NameNode API: http://localhost:8080"