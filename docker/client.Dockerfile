FROM python:3.9-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY common ./common
COPY client ./client
COPY setup.py .

# Install package
RUN pip install -e .

# Create working directory
RUN mkdir -p /workspace

WORKDIR /workspace

# Set entrypoint to CLI
ENTRYPOINT ["python", "-m", "client.cli"]