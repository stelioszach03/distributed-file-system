import React, { useState, useEffect } from 'react';
import styled from '@emotion/styled';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { 
  HardDrive, Upload, Download, Folder, File, Server, 
  Activity, Moon, Sun, Home, BarChart3, Settings,
  Trash2, Info, RefreshCw, Search, Grid3x3
} from 'lucide-react';
import FileExplorer from './components/FileExplorer';
import ClusterDashboard from './components/ClusterDashboard';
import StorageHeatmap from './components/StorageHeatmap';
import UploadModal from './components/UploadModal';
import api from './services/api';

const AppContainer = styled.div`
  min-height: 100vh;
  background: ${props => props.darkMode ? '#0a0a0a' : '#f5f5f5'};
  color: ${props => props.darkMode ? '#ffffff' : '#000000'};
  transition: all 0.3s ease;
`;

const Header = styled.header`
  background: ${props => props.darkMode ? '#1a1a1a' : '#ffffff'};
  border-bottom: 1px solid ${props => props.darkMode ? '#333' : '#e0e0e0'};
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: bold;
  color: #007bff;
`;

const Nav = styled.nav`
  display: flex;
  gap: 2rem;
  
  a {
    color: ${props => props.darkMode ? '#ccc' : '#666'};
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    transition: all 0.2s ease;
    
    &:hover {
      color: #007bff;
      background: ${props => props.darkMode ? '#222' : '#f0f0f0'};
    }
    
    &.active {
      color: #007bff;
      background: ${props => props.darkMode ? '#222' : '#e3f2fd'};
    }
  }
`;

const Actions = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const ThemeToggle = styled.button`
  background: transparent;
  border: none;
  color: ${props => props.darkMode ? '#ffd700' : '#666'};
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  transition: all 0.2s ease;
  
  &:hover {
    background: ${props => props.darkMode ? '#333' : '#e0e0e0'};
  }
`;

const MainContent = styled.main`
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
`;

const StatsBar = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
`;

const StatCard = styled.div`
  background: ${props => props.darkMode ? '#1a1a1a' : '#ffffff'};
  border: 1px solid ${props => props.darkMode ? '#333' : '#e0e0e0'};
  border-radius: 1rem;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  transition: transform 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 30px rgba(0,0,0,0.15);
  }
`;

const StatIcon = styled.div`
  width: 48px;
  height: 48px;
  background: ${props => props.color || '#007bff'};
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
`;

const StatInfo = styled.div`
  flex: 1;
  
  h3 {
    margin: 0;
    font-size: 0.875rem;
    color: ${props => props.darkMode ? '#aaa' : '#666'};
  }
  
  p {
    margin: 0.25rem 0 0 0;
    font-size: 1.5rem;
    font-weight: bold;
  }
`;

const Button = styled.button`
  background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
  box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 123, 255, 0.4);
  }
  
  &:active {
    transform: translateY(0);
  }
`;

function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [stats, setStats] = useState(null);
  const [showUpload, setShowUpload] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const data = await api.getClusterStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const formatBytes = (bytes) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const handleUploadComplete = () => {
    setShowUpload(false);
    setRefreshKey(prev => prev + 1);
  };

  return (
    <Router>
      <AppContainer darkMode={darkMode}>
        <Header darkMode={darkMode}>
          <Logo>
            <HardDrive size={32} />
            Distributed File System
          </Logo>
          
          <Nav darkMode={darkMode}>
            <NavLink to="/" end>
              <Home size={20} />
              Files
            </NavLink>
            <NavLink to="/cluster">
              <Server size={20} />
              Cluster
            </NavLink>
            <NavLink to="/analytics">
              <BarChart3 size={20} />
              Analytics
            </NavLink>
            <NavLink to="/settings">
              <Settings size={20} />
              Settings
            </NavLink>
          </Nav>
          
          <Actions>
            <Button onClick={() => setShowUpload(true)}>
              <Upload size={20} />
              Upload
            </Button>
            <ThemeToggle 
              darkMode={darkMode}
              onClick={() => setDarkMode(!darkMode)}
            >
              {darkMode ? <Sun size={24} /> : <Moon size={24} />}
            </ThemeToggle>
          </Actions>
        </Header>
        
        <MainContent>
          {stats && (
            <StatsBar>
              <StatCard darkMode={darkMode}>
                <StatIcon color="#28a745">
                  <Server size={24} />
                </StatIcon>
                <StatInfo darkMode={darkMode}>
                  <h3>Active Nodes</h3>
                  <p>{stats.alive_nodes}/{stats.total_nodes}</p>
                </StatInfo>
              </StatCard>
              
              <StatCard darkMode={darkMode}>
                <StatIcon color="#17a2b8">
                  <HardDrive size={24} />
                </StatIcon>
                <StatInfo darkMode={darkMode}>
                  <h3>Storage Used</h3>
                  <p>{formatBytes(stats.used_space)}</p>
                </StatInfo>
              </StatCard>
              
              <StatCard darkMode={darkMode}>
                <StatIcon color="#ffc107">
                  <Activity size={24} />
                </StatIcon>
                <StatInfo darkMode={darkMode}>
                  <h3>Total Chunks</h3>
                  <p>{stats.total_chunks}</p>
                </StatInfo>
              </StatCard>
              
              <StatCard darkMode={darkMode}>
                <StatIcon color="#dc3545">
                  <Grid3x3 size={24} />
                </StatIcon>
                <StatInfo darkMode={darkMode}>
                  <h3>Usage</h3>
                  <p>{stats.usage_percentage.toFixed(1)}%</p>
                </StatInfo>
              </StatCard>
            </StatsBar>
          )}
          
          <Routes>
            <Route path="/" element={
              <FileExplorer 
                darkMode={darkMode} 
                refreshKey={refreshKey}
                onRefresh={() => setRefreshKey(prev => prev + 1)}
              />
            } />
            <Route path="/cluster" element={
              <ClusterDashboard darkMode={darkMode} />
            } />
            <Route path="/analytics" element={
              <StorageHeatmap darkMode={darkMode} />
            } />
            <Route path="/settings" element={
              <div>Settings Page (Coming Soon)</div>
            } />
          </Routes>
        </MainContent>
        
        {showUpload && (
          <UploadModal 
            darkMode={darkMode}
            onClose={() => setShowUpload(false)}
            onComplete={handleUploadComplete}
          />
        )}
      </AppContainer>
    </Router>
  );
}

export default App;