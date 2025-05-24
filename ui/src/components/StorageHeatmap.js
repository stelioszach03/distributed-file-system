import React, { useState, useEffect } from 'react';
import styled from '@emotion/styled';
import { HardDrive, TrendingUp, AlertTriangle } from 'lucide-react';

const Container = styled.div`
  background: ${props => props.darkMode ? '#1a1a1a' : '#ffffff'};
  border: 1px solid ${props => props.darkMode ? '#333' : '#e0e0e0'};
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
`;

const Title = styled.h2`
  margin: 0 0 2rem 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: ${props => props.darkMode ? '#fff' : '#000'};
`;

const HeatmapGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
`;

const NodeCell = styled.div`
  aspect-ratio: 1;
  background: ${props => {
    const usage = props.usage;
    if (usage < 30) return '#28a745';
    if (usage < 60) return '#ffc107';
    if (usage < 80) return '#fd7e14';
    return '#dc3545';
  }};
  border-radius: 0.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  
  &:hover {
    transform: scale(1.05);
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
    z-index: 10;
  }
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, transparent 100%);
  }
`;

const NodeLabel = styled.div`
  font-size: 0.875rem;
  opacity: 0.9;
  z-index: 1;
`;

const NodeUsage = styled.div`
  font-size: 1.5rem;
  z-index: 1;
`;

const Legend = styled.div`
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-top: 2rem;
`;

const LegendItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const LegendColor = styled.div`
  width: 20px;
  height: 20px;
  border-radius: 0.25rem;
  background: ${props => props.color};
`;

const LegendLabel = styled.span`
  color: ${props => props.darkMode ? '#aaa' : '#666'};
  font-size: 0.875rem;
`;

const StatsSection = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid ${props => props.darkMode ? '#333' : '#e0e0e0'};
`;

const StatCard = styled.div`
  text-align: center;
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: bold;
  color: ${props => props.color || (props.darkMode ? '#fff' : '#000')};
`;

const StatLabel = styled.div`
  color: ${props => props.darkMode ? '#999' : '#666'};
  font-size: 0.875rem;
  margin-top: 0.5rem;
`;

function StorageHeatmap({ darkMode }) {
  const [nodes, setNodes] = useState([]);

  useEffect(() => {
    // Generate mock data for visualization
    const mockNodes = Array.from({ length: 12 }, (_, i) => ({
      id: `node-${i + 1}`,
      usage: Math.random() * 100,
      totalSpace: 1000 * 1024 * 1024 * 1024, // 1TB
      usedSpace: Math.random() * 1000 * 1024 * 1024 * 1024
    }));
    setNodes(mockNodes);
  }, []);

  const avgUsage = nodes.reduce((sum, node) => sum + node.usage, 0) / nodes.length || 0;
  const highUsageNodes = nodes.filter(node => node.usage > 80).length;
  const totalCapacity = nodes.reduce((sum, node) => sum + node.totalSpace, 0);

  const formatBytes = (bytes) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  return (
    <Container darkMode={darkMode}>
      <Title darkMode={darkMode}>
        <HardDrive size={28} />
        Storage Heatmap
      </Title>
      
      <HeatmapGrid>
        {nodes.map(node => (
          <NodeCell 
            key={node.id} 
            usage={node.usage}
            title={`${node.id}: ${formatBytes(node.usedSpace)} / ${formatBytes(node.totalSpace)}`}
          >
            <NodeLabel>{node.id}</NodeLabel>
            <NodeUsage>{Math.round(node.usage)}%</NodeUsage>
          </NodeCell>
        ))}
      </HeatmapGrid>
      
      <Legend>
        <LegendItem>
          <LegendColor color="#28a745" />
          <LegendLabel darkMode={darkMode}>Low (&lt;30%)</LegendLabel>
        </LegendItem>
        <LegendItem>
          <LegendColor color="#ffc107" />
          <LegendLabel darkMode={darkMode}>Medium (30-60%)</LegendLabel>
        </LegendItem>
        <LegendItem>
          <LegendColor color="#fd7e14" />
          <LegendLabel darkMode={darkMode}>High (60-80%)</LegendLabel>
        </LegendItem>
        <LegendItem>
          <LegendColor color="#dc3545" />
          <LegendLabel darkMode={darkMode}>Critical (&gt;80%)</LegendLabel>
        </LegendItem>
      </Legend>
      
      <StatsSection darkMode={darkMode}>
        <StatCard>
          <StatValue darkMode={darkMode}>{avgUsage.toFixed(1)}%</StatValue>
          <StatLabel darkMode={darkMode}>Average Usage</StatLabel>
        </StatCard>
        
        <StatCard>
          <StatValue color={highUsageNodes > 0 ? '#dc3545' : '#28a745'}>
            {highUsageNodes}
          </StatValue>
          <StatLabel darkMode={darkMode}>High Usage Nodes</StatLabel>
        </StatCard>
        
        <StatCard>
          <StatValue darkMode={darkMode}>{formatBytes(totalCapacity)}</StatValue>
          <StatLabel darkMode={darkMode}>Total Capacity</StatLabel>
        </StatCard>
        
        <StatCard>
          <StatValue color="#007bff">{nodes.length}</StatValue>
          <StatLabel darkMode={darkMode}>Total Nodes</StatLabel>
        </StatCard>
      </StatsSection>
    </Container>
  );
}

export default StorageHeatmap;