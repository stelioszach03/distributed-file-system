#!/bin/bash
# Master script to fix DFS issues

echo "=== DFS Master Fix Script ==="
echo ""
echo "This will try to fix your DFS installation step by step."
echo ""

# Check if other fix scripts exist
echo "Checking for fix scripts..."
SCRIPTS=(
    "fix_network_issue.sh"
    "run_from_host.sh"
    "fix_docker_network.sh"
    "search_solution.sh"
    "fix_all_issues.sh"
    "use_dfs_now.sh"
)

MISSING=0
for script in "${SCRIPTS[@]}"; do
    if [ ! -f "$script" ]; then
        echo "✗ Missing: $script"
        MISSING=$((MISSING + 1))
    else
        echo "✓ Found: $script"
    fi
done

if [ $MISSING -gt 0 ]; then
    echo ""
    echo "Some fix scripts are missing. Creating them now..."
    
    # Create any missing scripts
    [ ! -f "fix_network_issue.sh" ] && touch fix_network_issue.sh && chmod +x fix_network_issue.sh
    [ ! -f "run_from_host.sh" ] && touch run_from_host.sh && chmod +x run_from_host.sh
    [ ! -f "fix_docker_network.sh" ] && touch fix_docker_network.sh && chmod +x fix_docker_network.sh
    [ ! -f "search_solution.sh" ] && touch search_solution.sh && chmod +x search_solution.sh
    [ ! -f "fix_all_issues.sh" ] && touch fix_all_issues.sh && chmod +x fix_all_issues.sh
    [ ! -f "use_dfs_now.sh" ] && touch use_dfs_now.sh && chmod +x use_dfs_now.sh
    
    echo ""
    echo "Scripts created. Please copy the content from the artifacts into each script."
    echo "Then run this script again."
    exit 1
fi

# Function to run a fix and check result
run_fix() {
    local script=$1
    local description=$2
    
    echo ""
    echo "=== Running: $description ==="
    echo "Script: $script"
    echo ""
    
    if [ -f "$script" ]; then
        ./$script
        
        # Test if it worked
        if docker-compose exec -T client python -m client.cli stats 2>/dev/null | grep -q "Total Nodes"; then
            echo ""
            echo "✓ SUCCESS! The fix worked!"
            return 0
        fi
    else
        echo "✗ Script not found: $script"
    fi
    
    return 1
}

# Try fixes in order of likelihood to work
echo ""
echo "Starting fix attempts..."

# Fix 1: Try the comprehensive fix first
if run_fix "fix_all_issues.sh" "Comprehensive Fix (tries multiple solutions)"; then
    echo ""
    echo "=== DFS is now working! ==="
    echo "Use: docker-compose exec client python -m client.cli <command>"
    exit 0
fi

# Fix 2: Try network-specific fixes
if run_fix "fix_docker_network.sh" "Docker Network Fix"; then
    echo ""
    echo "=== DFS is now working! ==="
    exit 0
fi

# Fix 3: Try running from host
if run_fix "run_from_host.sh" "Host-based Client Setup"; then
    echo ""
    echo "=== DFS works from host! ==="
    echo "Use: ./dfs_host_client.py <command>"
    exit 0
fi

# If all fixes failed, provide workaround
echo ""
echo "=== All automatic fixes failed ==="
echo ""
echo "Running workaround setup..."
./use_dfs_now.sh

echo ""
echo "=== Manual Fix Instructions ==="
echo ""
echo "The automatic fixes didn't work, but the system is running."
echo "You have several options:"
echo ""
echo "1. Use the Web UI (recommended):"
echo "   http://localhost:3001"
echo ""
echo "2. Use the quick client:"
echo "   ./quickdfs.py <command>"
echo ""
echo "3. Debug the issue manually:"
echo "   - Check Docker logs: docker-compose logs"
echo "   - Restart Docker: sudo systemctl restart docker"
echo "   - Check network: docker network ls"
echo ""
echo "4. Report the issue with this information:"
echo "   - OS: $(uname -a)"
echo "   - Docker: $(docker --version)"
echo "   - Docker-Compose: $(docker-compose --version)"
echo ""

# Create a final working wrapper
cat > dfs_working << 'EOF'
#!/bin/bash
# Working DFS wrapper that tries multiple methods

# Method 1: Try quickdfs.py if it exists
if [ -f "./quickdfs.py" ]; then
    ./quickdfs.py "$@"
    exit $?
fi

# Method 2: Try host client
if [ -f "./dfs" ]; then
    ./dfs "$@"
    exit $?
fi

# Method 3: Try docker client
if [ -f "./dfs-docker" ]; then
    ./dfs-docker "$@"
    exit $?
fi

# Method 4: Direct Python
python3 -c "
import os
os.environ['NAMENODE_HOST'] = 'localhost'
import sys
sys.path.insert(0, '.')
from client.cli import main
main()
" "$@"
EOF
chmod +x dfs_working

echo "Created universal wrapper: ./dfs_working"
echo "This should work regardless of the networking issue."