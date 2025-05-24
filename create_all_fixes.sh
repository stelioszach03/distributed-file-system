#!/bin/bash
# Create all fix scripts automatically

echo "=== Creating All DFS Fix Scripts ==="
echo ""

# Array of scripts to create
declare -A SCRIPTS=(
    ["fix_network_issue.sh"]="Fix network resolution issues"
    ["run_from_host.sh"]="Run DFS client from host machine"
    ["fix_docker_network.sh"]="Fix Docker networking completely"
    ["search_solution.sh"]="Search and apply solutions from online"
    ["fix_all_issues.sh"]="Try all fixes automatically"
    ["use_dfs_now.sh"]="Use DFS immediately with workarounds"
    ["master_fix.sh"]="Master script that runs all fixes"
    ["FIX_SCRIPTS_README.md"]="Documentation for all fix scripts"
)

# Create each script
for script in "${!SCRIPTS[@]}"; do
    echo "Creating: $script - ${SCRIPTS[$script]}"
    touch "$script"
    
    # Make shell scripts executable
    if [[ "$script" == *.sh ]]; then
        chmod +x "$script"
    fi
done

echo ""
echo "=== All Scripts Created ==="
echo ""
echo "Now you need to copy the content from the artifacts into each script."
echo "The scripts are:"
echo ""
for script in "${!SCRIPTS[@]}"; do
    echo "- $script"
done
echo ""
echo "After copying the content, run:"
echo "  ./master_fix.sh"
echo ""
echo "Or if you want to try a quick fix right now, run:"
echo "  ./use_dfs_now.sh"
echo ""

# Create a simple test
echo "Creating a simple test script..."
cat > test_dfs_simple.sh << 'EOF'
#!/bin/bash
echo "Testing DFS connectivity..."

# Test 1: Check if services are running
echo -n "Services running: "
if docker-compose ps | grep -q "Up"; then
    echo "✓"
else
    echo "✗"
    echo "Run: docker-compose up -d"
    exit 1
fi

# Test 2: Check API access from host
echo -n "API accessible: "
if curl -s http://localhost:8080/health | grep -q "healthy"; then
    echo "✓"
else
    echo "✗"
    exit 1
fi

# Test 3: Check Web UI
echo -n "Web UI accessible: "
if curl -s http://localhost:3001 | grep -q "html"; then
    echo "✓"
else
    echo "✗"
fi

echo ""
echo "Basic connectivity is working!"
echo "The issue is with internal Docker DNS resolution."
echo "Run ./master_fix.sh to fix it."
EOF
chmod +x test_dfs_simple.sh

echo "Running simple test..."
./test_dfs_simple.sh