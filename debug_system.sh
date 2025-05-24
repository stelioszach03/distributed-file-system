#!/bin/bash
# Debug script to find the root cause of the issues

echo "=== Debugging Distributed File System ==="
echo ""

# Check container status
echo "1. Container Status:"
docker-compose ps
echo ""

# Check NameNode logs
echo "2. Recent NameNode Errors:"
docker-compose logs --tail=20 namenode | grep -E "(ERROR|error|Exception)" || echo "No recent errors found"
echo ""

# Check DataNode logs
echo "3. Recent DataNode Errors:"
for i in 1 2 3; do
    echo "DataNode $i:"
    docker-compose logs --tail=10 datanode$i | grep -E "(ERROR|error|Exception)" || echo "No errors"
done
echo ""

# Check network connectivity
echo "4. Network Connectivity Test:"
echo "From client to namenode:"
docker-compose exec -T client ping -c 1 namenode || echo "Failed to ping namenode"
echo ""
echo "From client to datanodes:"
for i in 1 2 3; do
    echo -n "datanode-$i: "
    docker-compose exec -T client ping -c 1 datanode-$i || echo "Failed"
done
echo ""

# Check API endpoints
echo "5. API Endpoint Tests:"
echo "NameNode health:"
curl -s http://localhost:8080/health | python3 -m json.tool || echo "Failed"
echo ""
echo "DataNode health:"
for i in 1 2 3; do
    echo "DataNode $i:"
    curl -s http://localhost:808$i/health | python3 -m json.tool | head -5 || echo "Failed"
done
echo ""

# Check chunk allocation
echo "6. Testing Chunk Allocation:"
curl -s -X POST http://localhost:8080/chunks/allocate \
  -H "Content-Type: application/json" \
  -d '{"size": 1024, "replication_factor": 1}' \
  | python3 -m json.tool || echo "Failed to allocate chunk"
echo ""

# Check the actual node registration
echo "7. Registered DataNodes:"
curl -s http://localhost:8080/datanodes | python3 -m json.tool || echo "Failed to get datanodes"
echo ""

# Show recent operations from all services
echo "8. Recent Operations (last 2 minutes):"
docker-compose logs --since 2m | grep -E "(upload|chunk|ERROR)" | tail -20
echo ""

echo "=== Debug Complete ==="
echo ""
echo "Look for any errors or connectivity issues above."
echo "Common issues:"
echo "- 'Name or service not known' = hostname resolution problem"
echo "- '500 Internal Server Error' = check namenode logs"
echo "- 'Connection refused' = service not ready or wrong port"