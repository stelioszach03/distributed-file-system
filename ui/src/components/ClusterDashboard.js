import React, { useState, useEffect } from 'react';
import styled from '@emotion/styled';
import { 
  Server, HardDrive, Activity, AlertCircle, CheckCircle,
  Cpu, Memory, Clock, RefreshCw
} from 'lucide-react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, 
         CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../services/api';

const Container = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1.5rem;
`;

const Card = styled.div`
  background: ${props => props.darkMode ? '#1a1a1a' : '#ffffff'};
  border: 1px solid ${props => props.darkMode ? '#333' : '#e0e0e0'};
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
`;

const CardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
`;

const CardTitle = styled.h3`
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: ${props => props.darkMode ? '#fff' : '#000'};
`;

const NodeList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const NodeItem = styled.div`
  background: ${props => props.darkMode ? '#0d0d0d' : '#f8f9fa'};
  border: 1px solid ${props => props.darkMode ? '#444' : '#e0e0e0'};
  border-radius: 0.5rem;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s ease;
  
  &:hover {
    transform: translateX(4px);
    border-color: #007bff;
  }
`;

const NodeInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const NodeStatus = styled.div`
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: ${props => props.alive ? '#28a745' : '#dc3545'};
  box-shadow: 0 0 10px ${props => props.alive ? '#28a745' : '#dc3545'};
`;

const NodeDetails = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const NodeName = styled.span`
  font-weight: 600;
  color: ${props => props.darkMode ? '#fff' : '#000'};
`;

const NodeStats = styled.span`
  font-size: 0.875rem;
  color: ${props => props.darkMode ? '#999' : '#666'};
`;

const MetricGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
`;

const Metric = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: ${props => props.darkMode ? '#222' : '#f0f0f0'};
  border-radius: 0.25rem;
  
  svg {
    color: #007bff;
  }
`;

const MetricLabel = styled.span`
  font-size: 0.75rem;
  color: ${props => props.darkMode ? '#999' : '#666'};
`;

const MetricValue = styled.span`
  font-weight: 600;
  color: ${props => props.darkMode ? '#fff' : '#000'};
`;

const ChartContainer = styled.div`
  height: 200px;
  margin-top: 1rem;
`;

function ClusterDashboard({ darkMode }) {
  const [datanodes, setDatanodes] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const nodes = await api.listDataNodes();
      setDatanodes(nodes);
      
      // Generate mock metrics for visualization
      const newMetric = {
        time: new Date().toLocaleTimeString(),
        cpu: Math.random() * 100,
        memory: Math.random() * 100,
        storage: Math.random() * 100
      };
      
      setMetrics(prev => [...prev.slice(-20), newMetric]);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load cluster data:', error);
      setLoading(false);
    }
  };

  const formatBytes = (bytes) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const getTimeSince = (timestamp) => {
    const seconds = Math.floor(Date.now() / 1000 - timestamp);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };

  return (
    <Container>
      <Card darkMode={darkMode}>
        <CardHeader>
          <CardTitle darkMode={darkMode}>
            <Server size={20} />
            DataNodes
          </CardTitle>
          <IconButton darkMode={darkMode} onClick={loadData}>
            <RefreshCw size={16} />
          </IconButton>
        </CardHeader>
        
        <NodeList>
          {datanodes.map(node => (
            <NodeItem key={node.node_id} darkMode={darkMode}>
              <NodeInfo>
                <NodeStatus alive={node.is_alive} />
                <NodeDetails>
                  <NodeName darkMode={darkMode}>{node.node_id}</NodeName>
                  <NodeStats darkMode={darkMode}>
                    {node.host}:{node.port} • {node.chunk_count} chunks
                  </NodeStats>
                </NodeDetails>
              </NodeInfo>
              
              <MetricGrid>
                <Metric darkMode={darkMode}>
                  <HardDrive size={14} />
                  <div>
                    <MetricLabel darkMode={darkMode}>Storage</MetricLabel>
                    <MetricValue darkMode={darkMode}>
                      {formatBytes(node.used_space)}
                    </MetricValue>
                  </div>
                </Metric>
                
                <Metric darkMode={darkMode}>
                  <Clock size={14} />
                  <div>
                    <MetricLabel darkMode={darkMode}>Last Seen</MetricLabel>
                    <MetricValue darkMode={darkMode}>
                      {getTimeSince(node.last_heartbeat)}
                    </MetricValue>
                  </div>
                </Metric>
              </MetricGrid>
            </NodeItem>
          ))}
        </NodeList>
      </Card>
      
      <Card darkMode={darkMode}>
        <CardHeader>
          <CardTitle darkMode={darkMode}>
            <Activity size={20} />
            System Metrics
          </CardTitle>
        </CardHeader>
        
        <ChartContainer>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#333' : '#e0e0e0'} />
              <XAxis dataKey="time" stroke={darkMode ? '#666' : '#999'} />
              <YAxis stroke={darkMode ? '#666' : '#999'} />
              <Tooltip 
                contentStyle={{ 
                  background: darkMode ? '#1a1a1a' : '#fff',
                  border: `1px solid ${darkMode ? '#333' : '#e0e0e0'}`
                }}
              />
              <Line type="monotone" dataKey="cpu" stroke="#007bff" strokeWidth={2} />
              <Line type="monotone" dataKey="memory" stroke="#28a745" strokeWidth={2} />
              <Line type="monotone" dataKey="storage" stroke="#ffc107" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      </Card>
      
      <Card darkMode={darkMode}>
        <CardHeader>
          <CardTitle darkMode={darkMode}>
            <Activity size={20} />
            Storage Distribution
          </CardTitle>
        </CardHeader>
        
        <ChartContainer>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#333' : '#e0e0e0'} />
              <XAxis dataKey="time" stroke={darkMode ? '#666' : '#999'} />
              <YAxis stroke={darkMode ? '#666' : '#999'} />
              <Tooltip 
                contentStyle={{ 
                  background: darkMode ? '#1a1a1a' : '#fff',
                  border: `1px solid ${darkMode ? '#333' : '#e0e0e0'}`
                }}
              />
              <Area 
                type="monotone" 
                dataKey="storage" 
                stroke="#007bff" 
                fill="#007bff" 
                fillOpacity={0.6} 
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartContainer>
      </Card>
    </Container>
  );
}

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

export default ClusterDashboard;