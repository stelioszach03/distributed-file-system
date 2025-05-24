#!/usr/bin/env python3
"""
Benchmark script for the distributed file system.
"""
import os
import time
import random
import argparse
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from client.api_client import DFSClient
from common.utils import format_bytes


def generate_test_file(size_mb: int) -> str:
    """Generate a test file of specified size."""
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    chunk_size = 1024 * 1024  # 1MB
    
    for _ in range(size_mb):
        data = bytes(random.getrandbits(8) for _ in range(chunk_size))
        temp_file.write(data)
    
    temp_file.close()
    return temp_file.name


def benchmark_upload(client: DFSClient, file_sizes: list, num_files: int):
    """Benchmark file uploads."""
    print("\n=== Upload Benchmark ===")
    results = []
    
    for size_mb in file_sizes:
        print(f"\nTesting {size_mb}MB files ({num_files} files)...")
        
        # Generate test files
        test_files = []
        for i in range(num_files):
            test_files.append({
                'path': generate_test_file(size_mb),
                'dfs_path': f'/benchmark/upload_{size_mb}MB_{i}.dat'
            })
        
        # Upload files
        start_time = time.time()
        
        for file_info in test_files:
            try:
                client.upload_file(file_info['path'], file_info['dfs_path'])
            except Exception as e:
                print(f"Upload failed: {e}")
        
        elapsed_time = time.time() - start_time
        total_size = size_mb * num_files * 1024 * 1024
        throughput = total_size / elapsed_time
        
        results.append({
            'file_size': f"{size_mb}MB",
            'num_files': num_files,
            'total_size': format_bytes(total_size),
            'time': f"{elapsed_time:.2f}s",
            'throughput': format_bytes(int(throughput)) + "/s"
        })
        
        # Clean up test files
        for file_info in test_files:
            os.unlink(file_info['path'])
    
    # Print results
    print("\nUpload Results:")
    print("-" * 80)
    print(f"{'File Size':<12} {'Files':<8} {'Total Size':<12} {'Time':<10} {'Throughput':<15}")
    print("-" * 80)
    for result in results:
        print(f"{result['file_size']:<12} {result['num_files']:<8} "
              f"{result['total_size']:<12} {result['time']:<10} {result['throughput']:<15}")


def benchmark_download(client: DFSClient, num_files: int):
    """Benchmark file downloads."""
    print("\n=== Download Benchmark ===")
    
    # List available files
    files = []
    try:
        contents = client.list_directory('/benchmark')
        files = [item for item in contents if item['type'] == 'file'][:num_files]
    except:
        print("No benchmark files found. Run upload benchmark first.")
        return
    
    if not files:
        print("No files to download.")
        return
    
    print(f"\nDownloading {len(files)} files...")
    
    # Download files
    start_time = time.time()
    total_size = 0
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for file_info in files:
            local_path = os.path.join(temp_dir, os.path.basename(file_info['path']))
            try:
                client.download_file(file_info['path'], local_path)
                total_size += file_info['size']
            except Exception as e:
                print(f"Download failed: {e}")
    
    elapsed_time = time.time() - start_time
    throughput = total_size / elapsed_time if elapsed_time > 0 else 0
    
    print(f"\nDownload Results:")
    print(f"Files downloaded: {len(files)}")
    print(f"Total size: {format_bytes(total_size)}")
    print(f"Time: {elapsed_time:.2f}s")
    print(f"Throughput: {format_bytes(int(throughput))}/s")


def benchmark_concurrent(client: DFSClient, num_threads: int, num_operations: int):
    """Benchmark concurrent operations."""
    print(f"\n=== Concurrent Operations Benchmark ===")
    print(f"Threads: {num_threads}, Operations per thread: {num_operations}")
    
    def worker(thread_id: int):
        """Worker function for concurrent operations."""
        results = {'uploads': 0, 'downloads': 0, 'errors': 0}
        
        for i in range(num_operations):
            try:
                # Alternate between upload and download
                if i % 2 == 0:
                    # Upload
                    test_file = generate_test_file(1)  # 1MB file
                    dfs_path = f'/benchmark/concurrent_{thread_id}_{i}.dat'
                    client.upload_file(test_file, dfs_path)
                    os.unlink(test_file)
                    results['uploads'] += 1
                else:
                    # Download
                    dfs_path = f'/benchmark/concurrent_{thread_id}_{i-1}.dat'
                    with tempfile.NamedTemporaryFile() as f:
                        client.download_file(dfs_path, f.name)
                    results['downloads'] += 1
                    
            except Exception as e:
                results['errors'] += 1
        
        return results
    
    # Run concurrent operations
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i) for i in range(num_threads)]
        
        total_results = {'uploads': 0, 'downloads': 0, 'errors': 0}
        for future in as_completed(futures):
            result = future.result()
            for key in total_results:
                total_results[key] += result[key]
    
    elapsed_time = time.time() - start_time
    total_ops = total_results['uploads'] + total_results['downloads']
    ops_per_second = total_ops / elapsed_time if elapsed_time > 0 else 0
    
    print(f"\nConcurrent Results:")
    print(f"Total operations: {total_ops}")
    print(f"Uploads: {total_results['uploads']}")
    print(f"Downloads: {total_results['downloads']}")
    print(f"Errors: {total_results['errors']}")
    print(f"Time: {elapsed_time:.2f}s")
    print(f"Operations/second: {ops_per_second:.2f}")


def main():
    """Main benchmark function."""
    parser = argparse.ArgumentParser(description='Benchmark DFS performance')
    parser.add_argument('--namenode', default='localhost', help='NameNode host')
    parser.add_argument('--port', type=int, default=8080, help='NameNode port')
    parser.add_argument('--upload', action='store_true', help='Run upload benchmark')
    parser.add_argument('--download', action='store_true', help='Run download benchmark')
    parser.add_argument('--concurrent', action='store_true', help='Run concurrent benchmark')
    parser.add_argument('--all', action='store_true', help='Run all benchmarks')
    
    args = parser.parse_args()
    
    # Create client
    client = DFSClient(args.namenode, args.port)
    
    # Create benchmark directory
    try:
        client.create_directory('/benchmark')
    except:
        pass  # Directory might already exist
    
    # Run benchmarks
    if args.upload or args.all:
        benchmark_upload(client, [1, 10, 50], 5)
    
    if args.download or args.all:
        benchmark_download(client, 10)
    
    if args.concurrent or args.all:
        benchmark_concurrent(client, 5, 10)
    
    if not any([args.upload, args.download, args.concurrent, args.all]):
        print("Please specify a benchmark to run (--upload, --download, --concurrent, or --all)")


if __name__ == '__main__':
    main()