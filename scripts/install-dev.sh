#!/bin/bash
# Development installation script for Committy

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Get the script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

# Change to the project root directory
cd "$PROJECT_ROOT" || { echo -e "${RED}Failed to navigate to project root!${NC}"; exit 1; }

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}Committy - Development Setup Script${NC}"
echo -e "${BLUE}=======================================${NC}\n"
echo -e "${YELLOW}Project root: ${PROJECT_ROOT}${NC}\n"

# Check if script is run with sudo (not recommended)
if [ "$(id -u)" = 0 ]; then
    echo -e "${YELLOW}Warning: This script is running with sudo privileges, which may cause permission issues.${NC}"
    echo -e "${YELLOW}It's recommended to run this script as a regular user.${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Setup aborted.${NC}"
        exit 1
    fi
fi

# Check if Python is installed
echo -e "${YELLOW}Checking if Python is installed...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python is not installed. Please install Python 3.10 or higher.${NC}"
    echo -e "For Ubuntu: ${YELLOW}sudo apt install python3 python3-pip${NC}"
    exit 1
else
    python_version=$(python3 --version)
    echo -e "${GREEN}✓ $python_version is installed${NC}"
    
    # Extract Python version number
    py_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    py_minor=$(python3 -c "import sys; print(sys.version_info.minor)")
fi

# Check if the appropriate Python venv package is installed
echo -e "${YELLOW}Checking if Python venv package is installed...${NC}"
if ! python3 -m venv --help &>/dev/null; then
    echo -e "${RED}Python venv package is not installed. Please install it:${NC}"
    echo -e "For Ubuntu/Debian: ${YELLOW}sudo apt install python3.12-venv${NC}"
    echo -e "or for the generic package: ${YELLOW}sudo apt install python3-venv${NC}"
    exit 1
else
    # Additional check: try to create a temp venv to ensure it works
    temp_venv=$(mktemp -d)
    if ! python3 -m venv "$temp_venv" &>/dev/null; then
        rm -rf "$temp_venv"
        echo -e "${RED}Python venv module is available but not working correctly.${NC}"
        echo -e "${RED}You need to install the specific venv package for your Python version:${NC}"
        echo -e "For Ubuntu/Debian: ${YELLOW}sudo apt install python3.${py_minor}-venv${NC}"
        exit 1
    fi
    rm -rf "$temp_venv"
    echo -e "${GREEN}✓ Python venv package is installed and working${NC}"
fi

# Create virtual environment with better error checking
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create virtual environment.${NC}"
    echo -e "${RED}On Ubuntu/Debian systems, you might need to install:${NC}"
    echo -e "${YELLOW}sudo apt install python3.${py_minor}-venv${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Verify venv was created properly
if [ ! -f "venv/bin/activate" ]; then
    echo -e "${RED}Virtual environment directory was created but activate script is missing.${NC}"
    echo -e "${RED}This might indicate an issue with your Python installation.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to activate virtual environment.${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
fi

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
echo -e "${YELLOW}Installing package in development mode...${NC}"
pip install -e .
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install package.${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Package installed in development mode${NC}"
fi

echo -e "${YELLOW}Installing basic requirements...${NC}"
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install dependencies.${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ Dependencies installed${NC}"
    fi
else
    echo -e "${YELLOW}requirements.txt not found, skipping...${NC}"
fi

echo -e "${YELLOW}Installing development requirements...${NC}"
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install development dependencies.${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ Development dependencies installed${NC}"
    fi
else
    echo -e "${YELLOW}requirements-dev.txt not found, skipping...${NC}"
fi

# Check if Ollama is installed
echo -e "${YELLOW}Checking for Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}Ollama not found. You have two options:${NC}"
    echo -e "1. Install Ollama (recommended for privacy) - See docs/OLLAMA_SETUP.md"
    echo -e "2. Configure an external AI API in your config file"
    echo -e "${YELLOW}Installation will continue...${NC}"
else
    echo -e "${GREEN}✓ Ollama is installed${NC}"
fi

# Create symlink for the CLI
echo -e "${YELLOW}Creating CLI symlink...${NC}"
if [ -f "${PROJECT_ROOT}/scripts/committy" ]; then
    chmod +x "${PROJECT_ROOT}/scripts/committy"
    mkdir -p ~/.local/bin

    # Check if symlink already exists
    if [ -L ~/.local/bin/committy ]; then
        echo -e "${YELLOW}Symlink already exists. Updating...${NC}"
        rm ~/.local/bin/committy
    fi

    # Create new symlink
    ln -s "${PROJECT_ROOT}/scripts/committy" ~/.local/bin/committy
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create symlink. You may need to create it manually.${NC}"
    else
        echo -e "${GREEN}✓ Symlink created at ~/.local/bin/committy${NC}"
    fi
else
    echo -e "${YELLOW}scripts/committy not found, skipping symlink creation...${NC}"
fi

# Create default config
echo -e "${YELLOW}Creating default configuration...${NC}"
mkdir -p ~/.config/committy
python -m committy --init-config
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create default configuration.${NC}"
    echo -e "${YELLOW}You may need to run 'committy --init-config' manually after installation.${NC}"
else
    echo -e "${GREEN}✓ Configuration created successfully${NC}"
fi

echo -e "\n${GREEN}=======================================${NC}"
echo -e "${GREEN}Committy development setup complete!${NC}"
echo -e "${GREEN}=======================================${NC}\n"

echo -e "To use Committy:"
echo -e "1. ${YELLOW}~/.local/bin/committy${NC} (or just ${YELLOW}committy${NC} if ~/.local/bin is in your PATH)"
echo -e "2. Update your PATH if needed: ${YELLOW}export PATH=\$PATH:~/.local/bin${NC}"
echo -e "3. To deactivate the virtual environment: ${YELLOW}deactivate${NC}"

echo -e "\n${BLUE}Happy committing!${NC}"