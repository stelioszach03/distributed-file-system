FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY common ./common
COPY datanode ./datanode
COPY setup.py .

# Install package
RUN pip install -e .

# Create data directory
RUN mkdir -p /data/dfs

# Expose ports
EXPOSE 9866 8081 9091

# Start DataNode
CMD ["python", "-m", "datanode.server"]