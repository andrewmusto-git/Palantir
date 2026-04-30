#!/bin/bash

################################################################################
# Virtual Environment Troubleshooting Script
# 
# This script diagnoses issues with the Python virtual environment setup
# for the Palantir Foundry integration
################################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Current directory: $SCRIPT_DIR"
echo

# Step 1: Check if venv directory exists
print_header "Step 1: Checking venv Directory"
if [ -d "$SCRIPT_DIR/venv" ]; then
    print_success "Virtual environment directory exists: $SCRIPT_DIR/venv"
else
    print_error "Virtual environment directory NOT found at: $SCRIPT_DIR/venv"
    echo "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi
echo

# Step 2: Check if activation script exists
print_header "Step 2: Checking Activation Script"
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    print_success "Activation script found: $SCRIPT_DIR/venv/bin/activate"
else
    print_error "Activation script NOT found"
    exit 1
fi
echo

# Step 3: Activate venv and check Python
print_header "Step 3: Activating venv and Checking Python"
source "$SCRIPT_DIR/venv/bin/activate"
print_success "Virtual environment activated"

PYTHON_PATH=$(which python)
print_info "Python executable: $PYTHON_PATH"

PYTHON_VERSION=$(python --version 2>&1)
print_info "Python version: $PYTHON_VERSION"

# Verify python is from venv
if [[ "$PYTHON_PATH" == *"venv"* ]]; then
    print_success "Using Python from venv ✓"
else
    print_warning "Not using Python from venv! Using: $PYTHON_PATH"
fi
echo

# Step 4: Check pip
print_header "Step 4: Checking pip"
PIP_PATH=$(which pip)
print_info "pip executable: $PIP_PATH"

PIP_VERSION=$(pip --version 2>&1)
print_info "pip version: $PIP_VERSION"

# Verify pip is from venv
if [[ "$PIP_PATH" == *"venv"* ]]; then
    print_success "Using pip from venv ✓"
else
    print_warning "Not using pip from venv! Using: $PIP_PATH"
fi
echo

# Step 5: Check installed packages
print_header "Step 5: Checking Installed Packages"
print_info "Checking for required packages..."
echo

pip list | grep -E "python-dotenv|requests|oaaclient" || print_warning "Some packages may be missing"
echo

# Step 6: Specific check for dotenv
print_header "Step 6: Checking python-dotenv"
if python -c "import dotenv; print(f'python-dotenv version: {dotenv.__version__}')" 2>/dev/null; then
    print_success "python-dotenv is installed and importable"
else
    print_error "python-dotenv is NOT installed or importable"
    print_info "Installing python-dotenv..."
    pip install python-dotenv
fi
echo

# Step 7: Check all requirements
print_header "Step 7: Installing All Requirements"
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    print_info "Found requirements.txt, installing dependencies..."
    pip install -r requirements.txt
    print_success "All requirements installed"
else
    print_error "requirements.txt not found at: $SCRIPT_DIR/requirements.txt"
fi
echo

# Step 8: Verify all imports
print_header "Step 8: Verifying All Imports"
python << 'EOF'
import sys

packages = [
    ('argparse', 'argparse'),
    ('json', 'json'),
    ('logging', 'logging'),
    ('os', 'os'),
    ('sys', 'sys'),
    ('time', 'time'),
    ('typing', 'typing'),
    ('urllib.parse', 'urllib.parse'),
    ('requests', 'requests'),
    ('dotenv', 'python-dotenv'),
    ('oaaclient', 'oaaclient'),
]

all_ok = True
for import_name, display_name in packages:
    try:
        __import__(import_name)
        print(f'✓ {display_name} is importable')
    except ImportError as e:
        print(f'✗ {display_name} FAILED to import: {e}')
        all_ok = False

if all_ok:
    print('\nAll imports successful!')
    sys.exit(0)
else:
    print('\nSome imports failed. See above.')
    sys.exit(1)
EOF

echo

# Step 9: Test script with --test flag
print_header "Step 9: Testing Script Execution"
if [ -f "$SCRIPT_DIR/.env" ]; then
    print_info "Running palantir_foundry.py --test to verify setup..."
    if python "$SCRIPT_DIR/palantir_foundry.py" --test; then
        print_success "Script executed successfully in test mode"
    else
        print_warning "Script test mode failed (this may be due to missing credentials, not venv issues)"
    fi
else
    print_warning ".env file not found - cannot test script execution"
    print_info "Create a .env file with your credentials to test the full setup"
fi
echo

# Final summary
print_header "Troubleshooting Summary"
print_success "Virtual environment setup appears to be working correctly!"
print_info "To use the venv in the future, run:"
echo "  source venv/bin/activate"
echo "  python palantir_foundry.py"
echo

deactivate

