"""
Setup script for the distributed file system.
"""
from setuptools import setup, find_packages

setup(
    name="distributed-file-system",
    version="0.1.0",
    description="A distributed file system implementation in Python",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "Flask>=2.3.3",
        "requests>=2.31.0",
        "prometheus-client>=0.17.1",
        "psutil>=5.9.5",
        "tabulate>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "dfs-namenode=namenode.server:main",
            "dfs-datanode=datanode.server:main",
            "dfs-cli=client.cli:main",
        ],
    },
    python_requires=">=3.8",
)