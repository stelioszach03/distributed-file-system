import React, { useState, useEffect } from 'react';
import styled from '@emotion/styled';
import { 
  Folder, File, Download, Trash2, Info, RefreshCw, 
  ChevronRight, Search, Grid, List
} from 'lucide-react';
import api from '../services/api';

const Container = styled.div`
  background: ${props => props.darkMode ? '#1a1a1a' : '#ffffff'};
  border: 1px solid ${props => props.darkMode ? '#333' : '#e0e0e0'};
  border-radius: 1rem;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
`;

const Toolbar = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid ${props => props.darkMode ? '#333' : '#e0e0e0'};
  background: ${props => props.darkMode ? '#0d0d0d' : '#f8f9fa'};
`;

const PathBar = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: ${props => props.darkMode ? '#aaa' : '#666'};
`;

const PathSegment = styled.span`
  cursor: pointer;
  transition: color 0.2s ease;
  
  &:hover {
    color: #007bff;
  }
`;

const Actions = styled.div`
  display: flex;
  gap: 0.5rem;
`;

const IconButton = styled.button`
  background: transparent;
  border: none;
  color: ${props => props.darkMode ? '#ccc' : '#666'};
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  transition: all 0.2s ease;
  
  &:hover {
    background: ${props => props.darkMode ? '#333' : '#e0e0e0'};
    color: #007bff;
  }
`;

const SearchBar = styled.div`
  position: relative;
  margin-right: 1rem;
`;

const SearchInput = styled.input`
  background: ${props => props.darkMode ? '#222' : '#f0f0f0'};
  border: 1px solid ${props => props.darkMode ? '#444' : '#ddd'};
  border-radius: 0.5rem;
  padding: 0.5rem 1rem 0.5rem 2.5rem;
  color: ${props => props.darkMode ? '#fff' : '#000'};
  width: 200px;
  transition: all 0.2s ease;
  
  &:focus {
    outline: none;
    border-color: #007bff;
    width: 250px;
  }
`;

const SearchIcon = styled(Search)`
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: ${props => props.darkMode ? '#666' : '#999'};
  size: 16px;
`;

const FileList = styled.div`
  padding: 1rem;
  min-height: 400px;
`;

const FileItem = styled.div`
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 0.25rem;
  
  &:hover {
    background: ${props => props.darkMode ? '#222' : '#f0f0f0'};
  }
  
  ${props => props.selected && `
    background: ${props.darkMode ? '#1e3a5f' : '#e3f2fd'};
    border: 1px solid #007bff;
  `}
`;

const FileIcon = styled.div`
  margin-right: 1rem;
  color: ${props => props.isFolder ? '#ffc107' : '#007bff'};
`;

const FileInfo = styled.div`
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const FileName = styled.span`
  font-weight: 500;
  color: ${props => props.darkMode ? '#fff' : '#000'};
`;

const FileSize = styled.span`
  color: ${props => props.darkMode ? '#999' : '#666'};
  font-size: 0.875rem;
`;

const FileActions = styled.div`
  display: flex;
  gap: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s ease;
  
  ${FileItem}:hover & {
    opacity: 1;
  }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 4rem;
  color: ${props => props.darkMode ? '#666' : '#999'};
  
  svg {
    margin-bottom: 1rem;
    opacity: 0.5;
  }
`;

const FileDetails = styled.div`
  display: flex;
  gap: 2rem;
  align-items: center;
  color: ${props => props.darkMode ? '#999' : '#666'};
  font-size: 0.875rem;
`;

const LoadingState = styled.div`
  text-align: center;
  padding: 4rem;
  color: ${props => props.darkMode ? '#666' : '#999'};
`;

function FileExplorer({ darkMode, refreshKey, onRefresh }) {
  const [currentPath, setCurrentPath] = useState('/');
  const [contents, setContents] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('list');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDirectory(currentPath);
  }, [currentPath, refreshKey]);

  const loadDirectory = async (path) => {
    setLoading(true);
    try {
      const data = await api.listDirectory(path);
      setContents(data);
      setSelectedFile(null);
    } catch (error) {
      console.error('Failed to load directory:', error);
      // If directory doesn't exist or error, show empty
      setContents([]);
    } finally {
      setLoading(false);
    }
  };

  const handleNavigate = (item) => {
    if (item.type === 'directory') {
      setCurrentPath(item.path);
    } else {
      setSelectedFile(item);
    }
  };

  const handleDownload = async (file) => {
    try {
      // Note: Real download implementation would require:
      // 1. Backend endpoint that serves file content
      // 2. Handling chunked downloads for large files
      // 3. Progress tracking
      
      // For now, we'll create a simple download link
      // In a real implementation, this would fetch actual file content
      const response = await fetch(`/api/files${file.path}/download`);
      
      if (!response.ok) {
        console.error('Download failed:', response.statusText);
        // For demo, create a dummy file
        const blob = new Blob([`Content of ${file.name}\nSize: ${file.size} bytes\nPath: ${file.path}`], 
                            { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = file.name;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        // Real implementation would handle the response blob
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = file.name;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Download failed:', error);
      // Fallback: create a demo file
      const blob = new Blob(
        [`Demo content for ${file.name}\n\nThis is a demonstration file.\nIn a real implementation, this would contain the actual file content from the distributed file system.`], 
        { type: 'text/plain' }
      );
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }
  };

  const handleDelete = async (file) => {
    if (window.confirm(`Delete ${file.name}?`)) {
      try {
        await api.deleteFile(file.path);
        onRefresh();
      } catch (error) {
        console.error('Delete failed:', error);
        alert(`Failed to delete ${file.name}: ${error.message}`);
      }
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '-';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return '-';
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
  };

  const filteredContents = contents.filter(item =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const pathSegments = currentPath.split('/').filter(Boolean);

  return (
    <Container darkMode={darkMode}>
      <Toolbar darkMode={darkMode}>
        <PathBar darkMode={darkMode}>
          <PathSegment onClick={() => setCurrentPath('/')}>
            Home
          </PathSegment>
          {pathSegments.map((segment, index) => (
            <React.Fragment key={index}>
              <ChevronRight size={16} />
              <PathSegment 
                onClick={() => {
                  const newPath = '/' + pathSegments.slice(0, index + 1).join('/');
                  setCurrentPath(newPath);
                }}
              >
                {segment}
              </PathSegment>
            </React.Fragment>
          ))}
        </PathBar>
        
        <Actions>
          <SearchBar>
            <SearchIcon darkMode={darkMode} size={16} />
            <SearchInput
              darkMode={darkMode}
              type="text"
              placeholder="Search files..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </SearchBar>
          
          <IconButton darkMode={darkMode} onClick={onRefresh} title="Refresh">
            <RefreshCw size={20} />
          </IconButton>
          
          <IconButton 
            darkMode={darkMode}
            onClick={() => setViewMode(viewMode === 'list' ? 'grid' : 'list')}
            title={viewMode === 'list' ? 'Grid view' : 'List view'}
          >
            {viewMode === 'list' ? <Grid size={20} /> : <List size={20} />}
          </IconButton>
        </Actions>
      </Toolbar>
      
      <FileList>
        {loading ? (
          <LoadingState darkMode={darkMode}>
            <RefreshCw size={48} style={{ animation: 'spin 1s linear infinite' }} />
            <p>Loading...</p>
          </LoadingState>
        ) : filteredContents.length === 0 ? (
          <EmptyState darkMode={darkMode}>
            <Folder size={48} />
            <p>{searchTerm ? 'No matching files found' : 'This folder is empty'}</p>
          </EmptyState>
        ) : (
          filteredContents.map((item) => (
            <FileItem
              key={item.path}
              darkMode={darkMode}
              selected={selectedFile?.path === item.path}
              onClick={() => handleNavigate(item)}
            >
              <FileIcon isFolder={item.type === 'directory'}>
                {item.type === 'directory' ? 
                  <Folder size={20} /> : 
                  <File size={20} />
                }
              </FileIcon>
              
              <FileInfo>
                <div>
                  <FileName darkMode={darkMode}>{item.name}</FileName>
                  {selectedFile?.path === item.path && item.type === 'file' && (
                    <FileDetails darkMode={darkMode}>
                      <span>Modified: {formatDate(item.modified_at)}</span>
                      <span>Created: {formatDate(item.created_at)}</span>
                    </FileDetails>
                  )}
                </div>
                <FileSize darkMode={darkMode}>
                  {formatBytes(item.size)}
                </FileSize>
              </FileInfo>
              
              <FileActions>
                {item.type === 'file' && (
                  <>
                    <IconButton 
                      darkMode={darkMode}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownload(item);
                      }}
                      title="Download"
                    >
                      <Download size={16} />
                    </IconButton>
                    <IconButton 
                      darkMode={darkMode}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(item);
                      }}
                      title="Delete"
                    >
                      <Trash2 size={16} />
                    </IconButton>
                  </>
                )}
              </FileActions>
            </FileItem>
          ))
        )}
      </FileList>
    </Container>
  );
}

// Add CSS animation for loading spinner
const style = document.createElement('style');
style.textContent = `
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;
document.head.appendChild(style);

export default FileExplorer;