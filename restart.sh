#!/bin/bash
echo "Restarting Distributed File System..."
docker-compose down
echo "Waiting 5 seconds..."
sleep 5
docker-compose up -d
echo "System restarted."
echo ""
echo "Access points:"
echo "• Web UI: http://localhost:3001"
echo "• Grafana: http://localhost:3000 (admin/admin)"
echo "• NameNode API: http://localhost:8080"
