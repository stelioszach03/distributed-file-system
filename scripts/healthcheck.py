#!/usr/bin/env python3
"""
Health check script for distributed file system components.
"""
import sys
import requests
import time
import argparse
from tabulate import tabulate


def check_namenode(host='localhost', port=8080):
    """Check NameNode health."""
    try:
        response = requests.get(f"http://{host}:{port}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def check_datanode(host='localhost', port=8081):
    """Check DataNode health."""
    try:
        response = requests.get(f"http://{host}:{port}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_cluster_stats(host='localhost', port=8080):
    """Get cluster statistics."""
    try:
        response = requests.get(f"http://{host}:{port}/cluster/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def get_datanode_info(host='localhost', port=8080):
    """Get DataNode information."""
    try:
        response = requests.get(f"http://{host}:{port}/datanodes", timeout=5)
        if response.status_code == 200:
            return response.json()['datanodes']
    except:
        pass
    return []


def format_bytes(bytes_value):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def main():
    parser = argparse.ArgumentParser(description='Check DFS health')
    parser.add_argument('--namenode', default='localhost', help='NameNode host')
    parser.add_argument('--port', type=int, default=8080, help='NameNode port')
    parser.add_argument('--watch', action='store_true', help='Continuously monitor')
    
    args = parser.parse_args()
    
    while True:
        # Clear screen if watching
        if args.watch:
            print("\033[2J\033[H")  # Clear screen
        
        print("=== Distributed File System Health Check ===")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Check NameNode
        namenode_status = check_namenode(args.namenode, args.port)
        print(f"NameNode: {'✓ HEALTHY' if namenode_status else '✗ DOWN'}")
        
        if namenode_status:
            # Get cluster stats
            stats = get_cluster_stats(args.namenode, args.port)
            if stats:
                print(f"\nCluster Statistics:")
                print(f"  Total Nodes: {stats['total_nodes']}")
                print(f"  Alive Nodes: {stats['alive_nodes']}")
                print(f"  Dead Nodes: {stats['dead_nodes']}")
                print(f"  Total Space: {format_bytes(stats['total_space'])}")
                print(f"  Used Space: {format_bytes(stats['used_space'])}")
                print(f"  Available Space: {format_bytes(stats['available_space'])}")
                print(f"  Usage: {stats['usage_percentage']:.1f}%")
                print(f"  Total Chunks: {stats['total_chunks']}")
            
            # Get DataNode info
            datanodes = get_datanode_info(args.namenode, args.port)
            if datanodes:
                print(f"\nDataNodes ({len(datanodes)}):")
                
                table_data = []
                for node in datanodes:
                    status = '✓' if node['is_alive'] else '✗'
                    last_seen = time.time() - node['last_heartbeat']
                    
                    table_data.append([
                        status,
                        node['node_id'],
                        f"{node['host']}:{node['port']}",
                        format_bytes(node['used_space']),
                        format_bytes(node['available_space']),
                        node['chunk_count'],
                        f"{last_seen:.0f}s ago"
                    ])
                
                headers = ['Status', 'Node ID', 'Address', 'Used', 'Available', 'Chunks', 'Last Seen']
                print(tabulate(table_data, headers=headers, tablefmt='grid'))
        
        # Check individual DataNodes
        print("\nDataNode Health Checks:")
        for i in range(1, 4):
            port = 8080 + i
            status = check_datanode(args.namenode, port)
            print(f"  DataNode {i} (port {port}): {'✓ HEALTHY' if status else '✗ DOWN'}")
        
        if not args.watch:
            break
        
        time.sleep(5)


if __name__ == '__main__':
    main()