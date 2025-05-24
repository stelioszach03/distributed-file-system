import React, { useState, useRef } from 'react';
import styled from '@emotion/styled';
import { Upload, X, File, AlertCircle, CheckCircle } from 'lucide-react';

const Overlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
`;

const Modal = styled.div`
  background: ${props => props.darkMode ? '#1a1a1a' : '#ffffff'};
  border-radius: 1rem;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
`;

const Header = styled.div`
  padding: 1.5rem;
  border-bottom: 1px solid ${props => props.darkMode ? '#333' : '#e0e0e0'};
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Title = styled.h3`
  margin: 0;
  color: ${props => props.darkMode ? '#fff' : '#000'};
`;

const CloseButton = styled.button`
  background: transparent;
  border: none;
  color: ${props => props.darkMode ? '#999' : '#666'};
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
  
  &:hover {
    background: ${props => props.darkMode ? '#333' : '#e0e0e0'};
  }
`;

const Content = styled.div`
  padding: 2rem;
`;

const DropZone = styled.div`
  border: 2px dashed ${props => props.darkMode ? '#444' : '#ddd'};
  border-radius: 0.5rem;
  padding: 3rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  
  ${props => props.isDragging && `
    border-color: #007bff;
    background: ${props.darkMode ? '#1e3a5f' : '#e3f2fd'};
  `}
  
  &:hover {
    border-color: #007bff;
  }
`;

const UploadIcon = styled(Upload)`
  color: ${props => props.darkMode ? '#666' : '#999'};
  margin-bottom: 1rem;
`;

const UploadText = styled.p`
  color: ${props => props.darkMode ? '#999' : '#666'};
  margin: 0;
`;

const FileInput = styled.input`
  display: none;
`;

const PathInput = styled.input`
  width: 100%;
  padding: 0.75rem;
  margin: 1rem 0;
  background: ${props => props.darkMode ? '#0d0d0d' : '#f8f9fa'};
  border: 1px solid ${props => props.darkMode ? '#333' : '#e0e0e0'};
  border-radius: 0.5rem;
  color: ${props => props.darkMode ? '#fff' : '#000'};
  
  &:focus {
    outline: none;
    border-color: #007bff;
  }
`;

const FileList = styled.div`
  margin-top: 1.5rem;
`;

const FileItem = styled.div`
  display: flex;
  align-items: center;
  padding: 0.75rem;
  background: ${props => props.darkMode ? '#0d0d0d' : '#f8f9fa'};
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
`;

const FileIcon = styled(File)`
  color: #007bff;
  margin-right: 0.75rem;
`;

const FileName = styled.span`
  flex: 1;
  color: ${props => props.darkMode ? '#fff' : '#000'};
`;

const FileSize = styled.span`
  color: ${props => props.darkMode ? '#999' : '#666'};
  font-size: 0.875rem;
`;

const Actions = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
`;

const Button = styled.button`
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  border: none;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const CancelButton = styled(Button)`
  background: ${props => props.darkMode ? '#333' : '#e0e0e0'};
  color: ${props => props.darkMode ? '#fff' : '#000'};
  
  &:hover:not(:disabled) {
    background: ${props => props.darkMode ? '#444' : '#d0d0d0'};
  }
`;

const UploadButton = styled(Button)`
  background: #007bff;
  color: white;
  
  &:hover:not(:disabled) {
    background: #0056b3;
  }
`;

const Progress = styled.div`
  margin-top: 1rem;
`;

const ProgressBar = styled.div`
  width: 100%;
  height: 4px;
  background: ${props => props.darkMode ? '#333' : '#e0e0e0'};
  border-radius: 2px;
  overflow: hidden;
`;

const ProgressFill = styled.div`
  height: 100%;
  background: #007bff;
  transition: width 0.3s ease;
  width: ${props => props.progress}%;
`;

const ProgressText = styled.p`
  text-align: center;
  color: ${props => props.darkMode ? '#999' : '#666'};
  font-size: 0.875rem;
  margin-top: 0.5rem;
`;

const Message = styled.div`
  padding: 0.75rem;
  border-radius: 0.5rem;
  margin-top: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  ${props => props.type === 'error' && `
    background: #dc3545;
    color: white;
  `}
  
  ${props => props.type === 'success' && `
    background: #28a745;
    color: white;
  `}
`;

const FileStatus = styled.div`
  margin-top: 1rem;
  max-height: 200px;
  overflow-y: auto;
`;

const StatusItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  color: ${props => props.darkMode ? '#999' : '#666'};
  font-size: 0.875rem;
  
  ${props => props.success && `
    color: #28a745;
  `}
  
  ${props => props.error && `
    color: #dc3545;
  `}
`;

const MaxSizeWarning = styled.div`
  background: #ffc107;
  color: #000;
  padding: 0.5rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

function UploadModal({ darkMode, onClose, onComplete }) {
  const [files, setFiles] = useState([]);
  const [dfsPath, setDfsPath] = useState('/');
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState(null);
  const [uploadStatus, setUploadStatus] = useState([]);
  const fileInputRef = useRef(null);

  const MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024; // 5GB

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    validateAndSetFiles(droppedFiles);
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    validateAndSetFiles(selectedFiles);
  };

  const validateAndSetFiles = (fileList) => {
    const validFiles = [];
    const errors = [];

    fileList.forEach(file => {
      if (file.size > MAX_FILE_SIZE) {
        errors.push(`${file.name} exceeds 5GB limit`);
      } else {
        validFiles.push(file);
      }
    });

    if (errors.length > 0) {
      setMessage({
        type: 'error',
        text: errors.join(', ')
      });
      setTimeout(() => setMessage(null), 5000);
    }

    setFiles(validFiles);
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    
    setUploading(true);
    setProgress(0);
    setMessage(null);
    setUploadStatus([]);
    
    try {
      let successCount = 0;
      let failCount = 0;
      
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const filePath = dfsPath.endsWith('/') 
          ? `${dfsPath}${file.name}` 
          : `${dfsPath}/${file.name}`;
        
        setUploadStatus(prev => [...prev, { 
          name: file.name, 
          status: 'uploading' 
        }]);
        
        try {
          // Real file upload with multipart/form-data
          const formData = new FormData();
          formData.append('file', file);
          formData.append('path', filePath);
          formData.append('replication_factor', '3');
          
          const response = await fetch('/api/files', {
            method: 'POST',
            body: formData
          });
          
          if (response.ok) {
            successCount++;
            setUploadStatus(prev => 
              prev.map(s => s.name === file.name 
                ? { ...s, status: 'success' } 
                : s
              )
            );
          } else {
            failCount++;
            const error = await response.json();
            setUploadStatus(prev => 
              prev.map(s => s.name === file.name 
                ? { ...s, status: 'error', error: error.error || 'Upload failed' } 
                : s
              )
            );
          }
          
        } catch (error) {
          failCount++;
          console.error(`Failed to upload ${file.name}:`, error);
          setUploadStatus(prev => 
            prev.map(s => s.name === file.name 
              ? { ...s, status: 'error', error: error.message } 
              : s
            )
          );
        }
        
        setProgress(((i + 1) / files.length) * 100);
      }
      
      // Final status message
      if (failCount === 0) {
        setMessage({
          type: 'success',
          text: `Successfully uploaded all ${successCount} files`
        });
        
        setTimeout(() => {
          onComplete();
        }, 1500);
      } else {
        setMessage({
          type: 'error',
          text: `Uploaded ${successCount} files, ${failCount} failed`
        });
        setUploading(false);
      }
      
    } catch (error) {
      console.error('Upload failed:', error);
      setMessage({
        type: 'error',
        text: error.message || 'Upload failed'
      });
      setUploading(false);
    }
  };

  const formatBytes = (bytes) => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const hasLargeFiles = files.some(f => f.size > 100 * 1024 * 1024); // 100MB

  return (
    <Overlay onClick={onClose}>
      <Modal darkMode={darkMode} onClick={(e) => e.stopPropagation()}>
        <Header darkMode={darkMode}>
          <Title darkMode={darkMode}>Upload Files</Title>
          <CloseButton darkMode={darkMode} onClick={onClose}>
            <X size={20} />
          </CloseButton>
        </Header>
        
        <Content>
          <DropZone
            darkMode={darkMode}
            isDragging={isDragging}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <UploadIcon darkMode={darkMode} size={48} />
            <UploadText darkMode={darkMode}>
              Drag files here or click to browse
            </UploadText>
          </DropZone>
          
          <FileInput
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileSelect}
          />
          
          <PathInput
            darkMode={darkMode}
            type="text"
            placeholder="DFS Path (e.g., /uploads)"
            value={dfsPath}
            onChange={(e) => setDfsPath(e.target.value)}
          />
          
          {files.length > 0 && (
            <FileList>
              {files.map((file, index) => (
                <FileItem key={index} darkMode={darkMode}>
                  <FileIcon size={20} />
                  <FileName darkMode={darkMode}>{file.name}</FileName>
                  <FileSize darkMode={darkMode}>
                    {formatBytes(file.size)}
                  </FileSize>
                </FileItem>
              ))}
            </FileList>
          )}
          
          {hasLargeFiles && !uploading && (
            <MaxSizeWarning>
              <AlertCircle size={16} />
              Large files detected. Upload may take several minutes.
            </MaxSizeWarning>
          )}
          
          {uploading && (
            <>
              <Progress>
                <ProgressBar darkMode={darkMode}>
                  <ProgressFill progress={progress} />
                </ProgressBar>
                <ProgressText darkMode={darkMode}>
                  Uploading... {Math.round(progress)}%
                </ProgressText>
              </Progress>
              
              {uploadStatus.length > 0 && (
                <FileStatus>
                  {uploadStatus.map((status, index) => (
                    <StatusItem 
                      key={index} 
                      darkMode={darkMode}
                      success={status.status === 'success'}
                      error={status.status === 'error'}
                    >
                      {status.status === 'success' && <CheckCircle size={16} />}
                      {status.status === 'error' && <AlertCircle size={16} />}
                      {status.status === 'uploading' && '⏳'}
                      {status.name}
                      {status.error && ` - ${status.error}`}
                    </StatusItem>
                  ))}
                </FileStatus>
              )}
            </>
          )}
          
          {message && (
            <Message type={message.type}>
              {message.type === 'error' ? (
                <AlertCircle size={20} />
              ) : (
                <CheckCircle size={20} />
              )}
              {message.text}
            </Message>
          )}
          
          <Actions>
            <CancelButton darkMode={darkMode} onClick={onClose} disabled={uploading}>
              Cancel
            </CancelButton>
            <UploadButton 
              onClick={handleUpload} 
              disabled={files.length === 0 || uploading || !dfsPath}
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </UploadButton>
          </Actions>
        </Content>
      </Modal>
    </Overlay>
  );
}

export default UploadModal;