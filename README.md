# Distributed File System (DFS)

<div align="center">
  
  ![Python](https://img.shields.io/badge/python-v3.9+-blue.svg)
  ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)
  ![React](https://img.shields.io/badge/react-%2320232a.svg?logo=react&logoColor=%2361DAFB)
  ![License](https://img.shields.io/badge/license-MIT-green.svg)
  ![Status](https://img.shields.io/badge/status-production%20ready-success)
  
  <h3>A production-ready distributed file system inspired by HDFS</h3>
  <p>Built with Python, React, and Docker - featuring real-time replication, monitoring, and fault tolerance</p>
  
  [Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [Usage](#-usage) • [API](#-api-reference) • [Contributing](#-contributing)
  
</div>

---

## 🎯 Overview

DFS is a fully functional distributed file system that provides reliable, scalable storage by automatically splitting files into chunks and distributing them across multiple storage nodes. **All operations use real data - no mocks or simulations.**

### Key Highlights

- 🔄 **Automatic Replication**: Configurable replication factor ensures data redundancy
- 📊 **Real-time Monitoring**: Live metrics via Prometheus & Grafana dashboards
- 🖥️ **Modern Web UI**: React-based interface for intuitive file management
- 🛡️ **Fault Tolerance**: Automatic failure detection and recovery
- 🚀 **High Performance**: Parallel chunk transfers and optimized I/O operations
- 📦 **Easy Deployment**: Single command setup with Docker Compose

## ✨ Features

### Core Functionality
- **Distributed Storage**: Files are split into 64MB chunks and distributed across DataNodes
- **Automatic Replication**: Default factor of 3 ensures data availability
- **Namespace Management**: Hierarchical file system with directory support
- **Chunk Management**: Intelligent placement and rebalancing of data chunks
- **Health Monitoring**: Continuous heartbeat monitoring with configurable timeouts

### User Interfaces
- **Web Dashboard**: 
  - File browser with upload/download capabilities
  - Real-time cluster statistics
  - Storage heatmap visualization
  - Live node health monitoring
- **Command Line Interface**:
  - Full file system operations (upload, download, ls, rm, mkdir)
  - Cluster administration commands
  - Performance benchmarking tools
- **REST API**: Comprehensive API for programmatic access

### Monitoring & Metrics
- **Prometheus Integration**: Collects metrics from all components
- **Grafana Dashboards**: Pre-configured dashboards for:
  - Cluster health overview
  - Storage utilization trends
  - Operation throughput
  - Node performance metrics

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
├─────────────┬─────────────┬─────────────┬────────────────────┤
│   Web UI    │     CLI     │  REST API   │   Python Client    │
│  (React)    │  (Python)   │   (Flask)   │    (Library)       │
└─────────────┴─────────────┴─────────────┴────────────────────┘
                               │
                               │ HTTP/REST
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                          NameNode                               │
├─────────────────────────────────────────────────────────────────┤
│  • Metadata Management (files, directories, chunks)             │
│  • Chunk Placement & Replication Strategy                       │
│  • DataNode Health Monitoring                                   │
│  • Namespace Operations                                         │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ TCP/Heartbeat
                               ▼
┌─────────────┬─────────────┬─────────────┬─────────────────────┐
│  DataNode 1 │  DataNode 2 │  DataNode 3 │    DataNode N...    │
├─────────────┼─────────────┼─────────────┼─────────────────────┤
│ • Local     │ • Local     │ • Local     │ • Local Storage     │
│   Storage   │   Storage   │   Storage   │ • Chunk Serving     │
│ • Chunk     │ • Chunk     │ • Chunk     │ • Replication       │
│   Serving   │   Serving   │   Serving   │ • Health Reporting  │
└─────────────┴─────────────┴─────────────┴─────────────────────┘
```

### Component Details

#### NameNode (Master)
- Manages all metadata operations
- Tracks chunk locations and replication
- Handles namespace (directory tree)
- Monitors DataNode health via heartbeats
- Makes chunk placement decisions

#### DataNodes (Workers)
- Store actual file chunks locally
- Serve chunk data to clients
- Perform peer-to-peer replication
- Report health metrics and storage stats
- Execute replication commands from NameNode

#### Client Interfaces
- **Web UI**: Modern React SPA with real-time updates
- **CLI**: Feature-complete command line tool
- **REST API**: JSON-based API for integrations
- **Python Client**: Library for programmatic access

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM recommended
- 10GB+ free disk space
- Linux/macOS/Windows with WSL2

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/stelioszach03/distributed-file-system.git
cd distributed-file-system
```

2. **Start the system**
```bash
./start.sh
```

3. **Verify deployment**
```bash
docker-compose ps
```

4. **Access interfaces**
- 🌐 **Web UI**: http://localhost:3001
- 📊 **Grafana**: http://localhost:3000 (admin/admin)
- 🔌 **API**: http://localhost:8080
- 📈 **Prometheus**: http://localhost:9094

## 📖 Usage

### Web Interface

Navigate to http://localhost:3001 for the intuitive web interface:

- **File Browser**: Upload, download, and manage files
- **Cluster Status**: View real-time node health and metrics
- **Storage Heatmap**: Visualize data distribution across nodes

### Command Line Interface

```bash
# Upload a file
docker-compose exec client python -m client.cli upload /local/file.txt /dfs/file.txt

# List directory contents
docker-compose exec client python -m client.cli ls /

# Download a file
docker-compose exec client python -m client.cli download /dfs/file.txt /local/file.txt

# Create directory
docker-compose exec client python -m client.cli mkdir /mydata

# Delete file
docker-compose exec client python -m client.cli rm /dfs/file.txt

# Get file info
docker-compose exec client python -m client.cli info /dfs/file.txt

# View cluster statistics
docker-compose exec client python -m client.cli stats
```

### Python Client Library

```python
from client.api_client import DFSClient

# Initialize client
client = DFSClient('localhost', 8080)

# Upload file
client.upload_file('/local/data.csv', '/dfs/data.csv', replication_factor=3)

# List directory
files = client.list_directory('/dfs')
for file in files:
    print(f"{file['name']} - {file['size']} bytes")

# Download file
client.download_file('/dfs/data.csv', '/local/downloaded.csv')

# Get cluster stats
stats = client.get_cluster_stats()
print(f"Total capacity: {stats['total_space']} bytes")
print(f"Used: {stats['used_space']} bytes ({stats['usage_percentage']:.1f}%)")
```

## 🔌 API Reference

### File Operations

**Upload File**
```http
POST /api/files
Content-Type: multipart/form-data

file: <binary>
path: /destination/path
replication_factor: 3
```

**Download File**
```http
GET /api/files/{path}/download
```

**Delete File**
```http
DELETE /api/files/{path}
```

**Get File Info**
```http
GET /api/files/{path}

Response:
{
  "path": "/example.txt",
  "size": 1048576,
  "chunks": [...],
  "created_at": 1234567890,
  "replication_factor": 3
}
```

### Directory Operations

**Create Directory**
```http
POST /api/directories
{
  "path": "/new/directory"
}
```

**List Directory**
```http
GET /api/directories/{path}
```

### Cluster Operations

**Get Cluster Stats**
```http
GET /api/cluster/stats

Response:
{
  "total_nodes": 3,
  "alive_nodes": 3,
  "total_space": 1081101176832,
  "used_space": 60553089024,
  "usage_percentage": 5.6
}
```

## ⚙️ Configuration

Key settings in `common/constants.py`:

```python
# Chunk size for file splitting
CHUNK_SIZE = 64 * 1024 * 1024  # 64MB

# Number of replicas for each chunk
REPLICATION_FACTOR = 3

# DataNode heartbeat settings
HEARTBEAT_INTERVAL = 3  # seconds
HEARTBEAT_TIMEOUT = 10  # seconds

# API settings
API_TIMEOUT = 30  # seconds
MAX_UPLOAD_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
```

## 📊 Performance & Benchmarks

Run the included benchmark suite:

```bash
python scripts/benchmark.py --all
```

Typical performance metrics:
- **Upload throughput**: 100-200 MB/s (depending on network)
- **Download throughput**: 150-300 MB/s
- **Replication speed**: 50-100 MB/s between nodes
- **Metadata operations**: <10ms latency

## 🔍 Monitoring

### Grafana Dashboards

Access pre-configured dashboards at http://localhost:3000:

1. **Cluster Overview**: System-wide health and statistics
2. **DataNode Metrics**: Per-node CPU, memory, and storage
3. **Operation Analytics**: Throughput and latency metrics
4. **Storage Distribution**: Visual representation of data placement

### Prometheus Metrics

Raw metrics available at http://localhost:9094:

- `dfs_datanode_storage_used_bytes`
- `dfs_datanode_chunk_count`
- `dfs_datanode_cpu_usage_percent`
- `dfs_datanode_chunk_operations_total`

## 🧪 Testing

### Run Unit Tests
```bash
docker-compose exec client pytest tests/unit/ -v
```

### Run Integration Tests
```bash
docker-compose exec client pytest tests/integration/ -v
```

### Run All Tests
```bash
docker-compose exec client pytest tests/ -v --cov=namenode --cov=datanode --cov=client
```

## 📝 System Management

### Starting & Stopping

```bash
# Start the system
./start.sh

# Stop the system
./stop.sh

# Restart the system
./restart.sh

# View logs
docker-compose logs -f [service_name]

# Stop and remove all data
docker-compose down -v
```

### Health Checks

```bash
# Check system health
python scripts/healthcheck.py

# Monitor in real-time
python scripts/healthcheck.py --watch
```

### Data Management

```bash
# Initialize with sample data
bash scripts/init_system.sh

# Backup metadata
docker-compose exec namenode tar -czf /backup/metadata.tar.gz /data/namenode

# Cleanup workspace
rm -rf workspace/*
```

## 🏗️ Production Deployment

### Considerations

1. **Hardware Requirements**:
   - NameNode: 8GB+ RAM, SSD storage for metadata
   - DataNodes: 4GB+ RAM, large HDD storage
   - Network: 1Gbps+ recommended

2. **High Availability**:
   - Current version has single NameNode (SPOF)
   - DataNode failures are handled automatically
   - Consider backup strategies for NameNode metadata

3. **Security**:
   - Add authentication to REST API
   - Enable TLS for all communications
   - Implement access control lists (ACLs)

4. **Scaling**:
   - Add DataNodes dynamically
   - Adjust replication factor based on needs
   - Monitor and rebalance as needed

> **Note on Storage Metrics**: In single-host deployments, storage metrics show aggregate capacity across all DataNodes. Since all nodes share the same filesystem, the total appears multiplied. In production multi-host deployments, this represents actual combined storage capacity.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md).

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run locally (for development)
python -m namenode.server  # In terminal 1
python -m datanode.server  # In terminal 2
python -m client.cli --help  # In terminal 3
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by [Apache Hadoop HDFS](https://hadoop.apache.org/)
- Built with [Flask](https://flask.palletsprojects.com/), [React](https://reactjs.org/), and [Docker](https://www.docker.com/)
- Monitoring stack: [Prometheus](https://prometheus.io/) & [Grafana](https://grafana.com/)
- UI components: [Lucide Icons](https://lucide.dev/) & [Recharts](https://recharts.org/)

## 📞 Support

- 📧 Email: stelios.zacharias@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/stelioszach03/distributed-file-system/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/stelioszach03/distributed-file-system/discussions)

---

<div align="center">
  <p>Made with ❤️ by <a href="https://github.com/stelioszach03">Stelios Zacharias</a></p>
  <p>⭐ Star this repository if you find it helpful!</p>
</div>
