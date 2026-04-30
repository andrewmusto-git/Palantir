#!/bin/bash

################################################################################
# Palantir Foundry to Veza OAA Integration Installer
#
# This script installs the Palantir Foundry-Veza integration with all 
# dependencies and prompts for credentials.
#
# Run with: curl -fsSL <url> | bash
################################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/andrewmusto-git/OAA_Veza.git"
INSTALL_DIR="$(pwd)/palantir-foundry-veza"
INTEGRATION_DIR="integrations/palantir-foundry"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Palantir Foundry to Veza Integration${NC}"
echo -e "${BLUE}Installation Script${NC}"
echo -e "${BLUE}================================================${NC}"

# Function to print colored output
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

# Check if running on Windows
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    print_error "This script is for Linux/macOS. Windows users should:"
    echo "1. Install Python 3.9+ from python.org"
    echo "2. Clone the repository manually"
    echo "3. Create a virtual environment: python -m venv venv"
    echo "4. Activate it: venv\Scripts\activate"
    echo "5. Install dependencies: pip install -r requirements.txt"
    echo "6. Configure .env file with your credentials"
    exit 1
fi

# Check Python installation
print_info "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    echo "Please install Python 3.9 or higher from: https://www.python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_success "Found Python $PYTHON_VERSION"

# Check if version is 3.9 or higher
REQUIRED_VERSION="3.9"
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"; then
    print_error "Python 3.9 or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

# Check Git installation
print_info "Checking Git installation..."
if ! command -v git &> /dev/null; then
    print_error "Git is not installed"
    echo "Please install Git from: https://git-scm.com"
    exit 1
fi

print_success "Git is installed"

# Create or overwrite installation directory
if [ -d "$INSTALL_DIR" ]; then
    print_info "Removing existing installation directory: $INSTALL_DIR"
    rm -rf "$INSTALL_DIR"
fi

print_info "Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

cd "$INSTALL_DIR"

# Clone repository if not already cloned
if [ ! -d ".git" ]; then
    print_info "Cloning repository..."
    if git clone "$REPO_URL" .; then
        print_success "Repository cloned successfully"
    else
        print_error "Failed to clone repository"
        exit 1
    fi
else
    print_info "Repository already cloned, pulling latest changes..."
    if git pull; then
        print_success "Repository updated successfully"
    else
        print_warning "Failed to pull latest changes"
    fi
fi

# Navigate to integration directory
INTEGRATION_PATH="${INSTALL_DIR}/${INTEGRATION_DIR}"
if [ ! -d "$INTEGRATION_PATH" ]; then
    print_error "Integration directory not found: $INTEGRATION_PATH"
    exit 1
fi

cd "$INTEGRATION_PATH"
print_success "Changed to integration directory: $(pwd)"

# Create Python virtual environment
print_info "Creating Python virtual environment..."
if python3 -m venv venv; then
    print_success "Virtual environment created"
else
    print_error "Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
python3 -m pip install --upgrade pip setuptools wheel > /dev/null 2>&1 || {
    print_warning "Failed to upgrade pip (continuing anyway)"
}

# Install dependencies
print_info "Installing dependencies from requirements.txt..."
if pip install -r requirements.txt; then
    print_success "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    deactivate
    exit 1
fi

# Prompt for credentials
print_info "Configuring integration credentials..."
echo

# Palantir Foundry configuration
echo -e "${YELLOW}Palantir Foundry Configuration${NC}"
read -p "Enter Palantir Foundry Base URL (e.g., https://your-instance.palantirfoundry.com): " FOUNDRY_BASE_URL

# Validate Foundry Base URL is not empty
while [ -z "$FOUNDRY_BASE_URL" ]; do
    print_error "Palantir Foundry Base URL cannot be empty"
    read -p "Enter Palantir Foundry Base URL (e.g., https://your-instance.palantirfoundry.com): " FOUNDRY_BASE_URL
done

# Prompt for API token (hidden input)
while true; do
    read -sp "Enter Palantir Foundry API Token (input hidden): " FOUNDRY_API_TOKEN
    echo
    if [ -z "$FOUNDRY_API_TOKEN" ]; then
        print_error "API Token cannot be empty"
        continue
    fi
    break
done

# Veza configuration
echo
echo -e "${YELLOW}Veza Configuration${NC}"
read -p "Enter Veza URL (e.g., https://your-instance.veza.com): " VEZA_URL

# Validate Veza URL is not empty
while [ -z "$VEZA_URL" ]; do
    print_error "Veza URL cannot be empty"
    read -p "Enter Veza URL (e.g., https://your-instance.veza.com): " VEZA_URL
done

# Prompt for API key (hidden input)
while true; do
    read -sp "Enter Veza API Key (input hidden): " VEZA_API_KEY
    echo
    if [ -z "$VEZA_API_KEY" ]; then
        print_error "API Key cannot be empty"
        continue
    fi
    break
done

# Create .env file
print_info "Creating .env configuration file..."
cat > .env << EOF
# Palantir Foundry Configuration
FOUNDRY_BASE_URL=${FOUNDRY_BASE_URL}
FOUNDRY_API_TOKEN=${FOUNDRY_API_TOKEN}

# Veza Configuration
VEZA_URL=${VEZA_URL}
VEZA_API_KEY=${VEZA_API_KEY}
EOF

print_success ".env file created"

# Test the connection
print_info "Testing connection to Palantir Foundry (dry-run)..."
if python3 palantir_foundry.py --dry-run --save-json --log-level INFO; then
    print_success "Connection test successful"
else
    print_error "Connection test failed"
    print_warning "Please verify your credentials in .env file"
fi

# Create wrapper script for cron
print_info "Creating integration wrapper script..."
cat > run_integration.sh << 'EOF'
#!/bin/bash
# Wrapper script for running the integration via cron

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Run integration
python3 palantir_foundry.py

# Deactivate virtual environment
deactivate
EOF

chmod +x run_integration.sh
print_success "Wrapper script created: run_integration.sh"

# Display next steps
echo
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Configuration file: $INTEGRATION_PATH/.env"
echo "2. Run integration manually:"
echo "   cd $INTEGRATION_PATH"
echo "   source venv/bin/activate"
echo "   python3 palantir_foundry.py"
echo
echo "3. Schedule with cron (optional):"
echo "   crontab -e"
echo "   # Add line to run daily at 2 AM:"
echo "   0 2 * * * cd $INTEGRATION_PATH && source venv/bin/activate && python3 palantir_foundry.py"
echo
echo -e "${BLUE}Support:${NC}"
echo "- Integration directory: $INTEGRATION_PATH"
echo "- Logs: $INTEGRATION_PATH/logs/"
echo "- README: $INTEGRATION_PATH/README.md"
echo

print_success "Installation completed successfully!"
