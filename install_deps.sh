#!/bin/bash
# Install system dependencies for running scripts

echo "=== Installing System Dependencies ==="

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        echo "Installing Python packages for Debian/Ubuntu..."
        sudo apt-get update
        sudo apt-get install -y python3-pip python3-requests python3-tabulate
    elif command -v yum &> /dev/null; then
        # RedHat/CentOS
        echo "Installing Python packages for RedHat/CentOS..."
        sudo yum install -y python3-pip
        sudo pip3 install requests tabulate
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        echo "Installing Python packages for Arch Linux..."
        sudo pacman -S python-pip python-requests python-tabulate
    else
        echo "Unknown Linux distribution. Installing with pip3..."
        pip3 install --user requests tabulate
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # Mac OSX
    echo "Installing Python packages for macOS..."
    pip3 install --user requests tabulate
else
    # Windows or other
    echo "Installing Python packages..."
    pip3 install --user requests tabulate
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Now you can run:"
echo "  bash fix_and_run.sh"