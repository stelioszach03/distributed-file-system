#!/usr/bin/env python3
"""Quick DFS Client - Works around networking issues"""
import requests
import sys
import os
import json

# The NameNode is accessible at localhost:8080 from the host
API_URL = "http://localhost:8080"

def upload_file(local_path, remote_path):
    """Upload a file by creating it in DFS"""
    # First create the file entry
    resp = requests.post(f"{API_URL}/files", 
                        json={"path": remote_path, "replication_factor": 3})
    if resp.status_code == 201:
        print(f"✓ Created file entry: {remote_path}")
        # In a real implementation, we'd upload chunks here
        # For now, just mark as success
        print(f"✓ File ready for upload: {local_path} -> {remote_path}")
    else:
        print(f"✗ Failed to create file: {resp.text}")

def list_files(path="/"):
    """List files in directory"""
    resp = requests.get(f"{API_URL}/directories{path}")
    if resp.status_code == 200:
        contents = resp.json()["contents"]
        print(f"\nContents of {path}:")
        for item in contents:
            type_char = "D" if item["type"] == "directory" else "F"
            print(f"  [{type_char}] {item['name']}")
    else:
        print(f"✗ Failed to list directory: {resp.text}")

def create_dir(path):
    """Create a directory"""
    resp = requests.post(f"{API_URL}/directories", json={"path": path})
    if resp.status_code == 201:
        print(f"✓ Created directory: {path}")
    else:
        print(f"✗ Failed to create directory: {resp.text}")

def get_stats():
    """Get cluster statistics"""
    resp = requests.get(f"{API_URL}/cluster/stats")
    if resp.status_code == 200:
        stats = resp.json()
        print("\nCluster Statistics:")
        print(f"  Active Nodes: {stats['alive_nodes']}/{stats['total_nodes']}")
        print(f"  Storage: {stats['used_space']/(1024**3):.2f}GB / {stats['total_space']/(1024**3):.2f}GB")
        print(f"  Total Chunks: {stats['total_chunks']}")
    else:
        print(f"✗ Failed to get stats: {resp.text}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  ./quickdfs.py stats")
        print("  ./quickdfs.py ls [path]")
        print("  ./quickdfs.py mkdir <path>")
        print("  ./quickdfs.py upload <local_file> <remote_path>")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "stats":
        get_stats()
    elif cmd == "ls":
        path = sys.argv[2] if len(sys.argv) > 2 else "/"
        list_files(path)
    elif cmd == "mkdir" and len(sys.argv) > 2:
        create_dir(sys.argv[2])
    elif cmd == "upload" and len(sys.argv) > 3:
        upload_file(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
