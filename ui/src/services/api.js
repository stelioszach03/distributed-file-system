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

    // Add response interceptor for better error handling
    this.client.interceptors.response.use(
      response => response,
      error => {
        // Log errors for debugging
        console.error('API Error:', error);
        
        // Add more context to the error
        if (error.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          error.message = `Server error: ${error.response.status} - ${error.response.data?.error || error.response.statusText}`;
        } else if (error.request) {
          // The request was made but no response was received
          error.message = 'No response from server. Please check if the server is running.';
        } else {
          // Something happened in setting up the request that triggered an Error
          error.message = `Request error: ${error.message}`;
        }
        
        return Promise.reject(error);
      }
    );
  }

  // File operations
  async createFile(path, replicationFactor = 3) {
    const response = await this.client.post('/files', {
      path,
      replication_factor: replicationFactor,
    });
    return response.data;
  }

  async uploadFile(file, path, replicationFactor = 3) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('path', path);
    formData.append('replication_factor', replicationFactor);

    const response = await this.client.post('/files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      // Track upload progress
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        console.log(`Upload progress: ${percentCompleted}%`);
      },
    });
    return response.data;
  }

  async getFileInfo(path) {
    const response = await this.client.get(`/files${path}`);
    return response.data;
  }

  async downloadFile(path) {
    const response = await this.client.get(`/files${path}/download`, {
      responseType: 'blob',
      // Track download progress
      onDownloadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          console.log(`Download progress: ${percentCompleted}%`);
        }
      },
    });
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

  async getChunkStatus() {
    const response = await this.client.get('/chunks/status');
    return response.data;
  }

  // Health check
  async checkHealth() {
    const response = await this.client.get('/health');
    return response.data;
  }
}

export default new ApiService();