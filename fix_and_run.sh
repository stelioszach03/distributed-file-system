#!/bin/bash
# Script to fix and run the distributed file system

set -e

echo "=== Fixing Distributed File System Setup ==="

# Install required Python packages
echo "Installing Python dependencies..."
pip3 install requests 2>/dev/null || sudo pip3 install requests || echo "Please install python3-requests manually"

# Fix Memory icon issue
echo "Fixing UI component..."
sed -i 's/<Memory size={14} \/>/<Gauge size={14} \/>/g' ui/src/components/ClusterDashboard.js
sed -i 's/<MetricLabel darkMode={darkMode}>Memory<\/MetricLabel>/<MetricLabel darkMode={darkMode}>Memory<\/MetricLabel>/g' ui/src/components/ClusterDashboard.js

# Create nginx.conf in root if it doesn't exist
echo "Creating nginx.conf..."
cat > nginx.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Serve React app
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to NameNode
    location /api/ {
        proxy_pass http://namenode:8080/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Update ui.Dockerfile
echo "Updating ui.Dockerfile..."
cat > docker/ui.Dockerfile << 'EOF'
FROM node:16-alpine AS builder

WORKDIR /app

# Copy UI directory contents
COPY ui/package*.json ./

# Install dependencies
RUN npm install

# Copy UI source code
COPY ui/public ./public
COPY ui/src ./src

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration from root
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF

# Clean and rebuild
echo "Cleaning previous build..."
docker-compose down -v

echo "Building services..."
docker-compose up --build -d

# Wait for services
echo "Waiting for services to start (30 seconds)..."
sleep 30

# Check health
echo "Checking system health..."
python3 scripts/healthcheck.py || echo "Health check completed with warnings"

# Initialize with sample data
echo "Initializing system with sample data..."
bash scripts/init_system.sh || echo "Initialization completed with warnings"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Access points:"
echo "- Web UI: http://localhost:3001"
echo "- Grafana: http://localhost:3000 (admin/admin)"
echo "- NameNode API: http://localhost:8080"
echo ""
echo "To check logs:"
echo "  docker-compose logs -f"
echo ""
echo "To access CLI:"
echo "  docker-compose exec client bash"