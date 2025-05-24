#!/usr/bin/env python3
"""
Command-line interface for the distributed file system.
"""
import os
import sys
import argparse
from tabulate import tabulate
from .api_client import DFSClient
from common.utils import format_bytes


def create_parser():
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description='Distributed File System Client',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--namenode',
        default='namenode',
        help='NameNode host (default: namenode)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='NameNode API port (default: 8080)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload a file')
    upload_parser.add_argument('local_path', help='Local file path')
    upload_parser.add_argument('dfs_path', help='DFS file path')
    upload_parser.add_argument(
        '--replication',
        type=int,
        default=3,
        help='Replication factor (default: 3)'
    )
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download a file')
    download_parser.add_argument('dfs_path', help='DFS file path')
    download_parser.add_argument('local_path', help='Local file path')
    
    # List command
    ls_parser = subparsers.add_parser('ls', help='List directory contents')
    ls_parser.add_argument('path', nargs='?', default='/', help='Directory path')
    
    # Delete command
    rm_parser = subparsers.add_parser('rm', help='Delete a file')
    rm_parser.add_argument('path', help='File path')
    
    # Mkdir command
    mkdir_parser = subparsers.add_parser('mkdir', help='Create a directory')
    mkdir_parser.add_argument('path', help='Directory path')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get file information')
    info_parser.add_argument('path', help='File path')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Get cluster statistics')
    
    return parser


def handle_upload(client: DFSClient, args):
    """Handle file upload."""
    if not os.path.exists(args.local_path):
        print(f"Error: Local file not found: {args.local_path}")
        return 1
    
    try:
        client.upload_file(args.local_path, args.dfs_path, args.replication)
        print(f"Successfully uploaded {args.local_path} to {args.dfs_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def handle_download(client: DFSClient, args):
    """Handle file download."""
    try:
        client.download_file(args.dfs_path, args.local_path)
        print(f"Successfully downloaded {args.dfs_path} to {args.local_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def handle_list(client: DFSClient, args):
    """Handle directory listing."""
    try:
        contents = client.list_directory(args.path)
        
        if not contents:
            print(f"Directory is empty: {args.path}")
            return 0
        
        # Format output
        table_data = []
        for item in contents:
            if item['type'] == 'file':
                size = format_bytes(item['size'])
            else:
                size = '-'
            
            table_data.append([
                item['type'][0].upper(),  # F or D
                item['name'],
                size
            ])
        
        print(tabulate(table_data, headers=['Type', 'Name', 'Size']))
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


def handle_delete(client: DFSClient, args):
    """Handle file deletion."""
    try:
        # Confirm deletion
        response = input(f"Delete {args.path}? [y/N]: ")
        if response.lower() != 'y':
            print("Cancelled")
            return 0
        
        client.delete_file(args.path)
        print(f"Successfully deleted {args.path}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def handle_mkdir(client: DFSClient, args):
    """Handle directory creation."""
    try:
        client.create_directory(args.path)
        print(f"Successfully created directory {args.path}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def handle_info(client: DFSClient, args):
    """Handle file info display."""
    try:
        info = client.get_file_info(args.path)
        if not info:
            print(f"File not found: {args.path}")
            return 1
        
        print(f"File: {info['path']}")
        print(f"Size: {format_bytes(info['size'])}")
        print(f"Chunks: {len(info['chunks'])}")
        print(f"Replication Factor: {info['replication_factor']}")
        print(f"Created: {info['created_at']}")
        print(f"Modified: {info['modified_at']}")
        
        if info['chunks']:
            print("\nChunk Details:")
            table_data = []
            for i, chunk in enumerate(info['chunks']):
                table_data.append([
                    i + 1,
                    chunk['chunk_id'][:8] + '...',
                    format_bytes(chunk['size']),
                    len(chunk['locations'])
                ])
            
            print(tabulate(table_data, 
                         headers=['#', 'Chunk ID', 'Size', 'Replicas']))
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


def handle_stats(client: DFSClient, args):
    """Handle cluster stats display."""
    try:
        stats = client.get_cluster_stats()
        
        print("Cluster Statistics")
        print("-" * 40)
        print(f"Total Nodes: {stats['total_nodes']}")
        print(f"Alive Nodes: {stats['alive_nodes']}")
        print(f"Dead Nodes: {stats['dead_nodes']}")
        print(f"Total Space: {format_bytes(stats['total_space'])}")
        print(f"Used Space: {format_bytes(stats['used_space'])}")
        print(f"Available Space: {format_bytes(stats['available_space'])}")
        print(f"Usage: {stats['usage_percentage']:.1f}%")
        print(f"Total Chunks: {stats['total_chunks']}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Create client
    client = DFSClient(args.namenode, args.port)
    
    # Handle commands
    handlers = {
        'upload': handle_upload,
        'download': handle_download,
        'ls': handle_list,
        'rm': handle_delete,
        'mkdir': handle_mkdir,
        'info': handle_info,
        'stats': handle_stats
    }
    
    handler = handlers.get(args.command)
    if handler:
        return handler(client, args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())