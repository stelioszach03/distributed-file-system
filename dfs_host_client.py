#!/usr/bin/env python3
import sys
import os

# Set the NAMENODE_HOST to localhost since we're running from host
os.environ['NAMENODE_HOST'] = 'localhost'

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the CLI
from client.cli import main

if __name__ == '__main__':
    sys.exit(main())
