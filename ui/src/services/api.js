import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // File operations
  async createFile(path, replicationFactor = 3) {
    const response = await this.client.post('/files', {
      path,
      replication_factor: replicationFactor,
    });
    return response.data;
  }

  async getFileInfo(path) {
    const response = await this.client.get(`/files${path}`);
    return response.data;
  }

  async deleteFile(path) {
    const response = await this.client.delete(`/files${path}`);
    return response.data;
  }

  // Directory operations
  async createDirectory(path) {
    const response = await this.client.post('/directories', { path });
    return response.data;
  }

  async listDirectory(path = '/') {
    const response = await this.client.get(`/directories${path}`);
    return response.data.contents;
  }

  // Cluster operations
  async getClusterStats() {
    const response = await this.client.get('/cluster/stats');
    return response.data;
  }

  async listDataNodes() {
    const response = await this.client.get('/datanodes');
    return response.data.datanodes;
  }

  // Chunk operations
  async allocateChunk(size, replicationFactor = 3) {
    const response = await this.client.post('/chunks/allocate', {
      size,
      replication_factor: replicationFactor,
    });
    return response.data;
  }
}

export default new ApiService();