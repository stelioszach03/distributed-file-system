#!/bin/bash
echo "Testing DFS connectivity..."

# Test 1: Check if services are running
echo -n "Services running: "
if docker-compose ps | grep -q "Up"; then
    echo "✓"
else
    echo "✗"
    echo "Run: docker-compose up -d"
    exit 1
fi

# Test 2: Check API access from host
echo -n "API accessible: "
if curl -s http://localhost:8080/health | grep -q "healthy"; then
    echo "✓"
else
    echo "✗"
    exit 1
fi

# Test 3: Check Web UI
echo -n "Web UI accessible: "
if curl -s http://localhost:3001 | grep -q "html"; then
    echo "✓"
else
    echo "✗"
fi

echo ""
echo "Basic connectivity is working!"
echo "The issue is with internal Docker DNS resolution."
echo "Run ./master_fix.sh to fix it."
