#!/bin/bash
echo "=== DFS Demo Usage ==="
echo ""

# Check if API is accessible
echo "1. Checking API access..."
curl -s http://localhost:8080/health | python3 -m json.tool

echo ""
echo "2. Getting cluster stats..."
./quickdfs.py stats

echo ""
echo "3. Creating directories..."
./quickdfs.py mkdir /demo
./quickdfs.py mkdir /demo/files
./quickdfs.py mkdir /demo/backups

echo ""
echo "4. Listing directories..."
./quickdfs.py ls /
./quickdfs.py ls /demo

echo ""
echo "5. Creating test files..."
echo "This is a demo file" > demo1.txt
echo "Another test file with more content" > demo2.txt

echo ""
echo "6. Uploading files..."
./quickdfs.py upload demo1.txt /demo/files/demo1.txt
./quickdfs.py upload demo2.txt /demo/files/demo2.txt

echo ""
echo "7. Listing uploaded files..."
./quickdfs.py ls /demo/files

# Cleanup
rm -f demo1.txt demo2.txt

echo ""
echo "=== Demo Complete ==="
echo ""
echo "You can also access:"
echo "- Web UI: http://localhost:3001"
echo "- API: http://localhost:8080"
echo "- Grafana: http://localhost:3000"
