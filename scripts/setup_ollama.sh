#!/bin/bash
# setup_ollama.sh - Helper script to install and configure Ollama for AutoCommit
# This script is provided for convenience and is not required for AutoCommit to work.

set -e  # Exit on any error

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Default model
DEFAULT_MODEL="gemma3:12b"
MODEL=${1:-$DEFAULT_MODEL}

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}AutoCommit - Ollama Setup Script${NC}"
echo -e "${BLUE}=======================================${NC}\n"

# Check if script is run with sudo (not recommended)
if [ "$(id -u)" = 0 ]; then
    echo -e "${YELLOW}This script is running with sudo privileges, which isn't recommended.${NC}"
    echo -e "${YELLOW}Ollama should be installed as a regular user.${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Setup aborted.${NC}"
        exit 1
    fi
fi

# Step 1: Check if Ollama is already installed
echo -e "\n${BLUE}Step 1: Checking if Ollama is already installed...${NC}"
if command -v ollama &> /dev/null; then
    OLLAMA_VERSION=$(ollama --version 2>&1)
    echo -e "${GREEN}✓ Ollama is already installed (${OLLAMA_VERSION})${NC}"
else
    echo -e "${YELLOW}Ollama is not installed. Installing now...${NC}"
    
    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Detected Linux system."
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo -e "${RED}Unsupported operating system. Please install Ollama manually.${NC}"
        echo "Visit https://ollama.com/download for installation instructions."
        exit 1
    fi
    
    # Verify installation
    if command -v ollama &> /dev/null; then
        OLLAMA_VERSION=$(ollama --version 2>&1)
        echo -e "${GREEN}✓ Ollama installed successfully (${OLLAMA_VERSION})${NC}"
    else
        echo -e "${RED}Failed to install Ollama. Please install manually.${NC}"
        echo "Visit https://ollama.com/download for installation instructions."
        exit 1
    fi
fi

# Step 2: Check if Ollama service is running
echo -e "\n${BLUE}Step 2: Checking if Ollama service is running...${NC}"
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${GREEN}✓ Ollama service is already running${NC}"
else
    echo -e "${YELLOW}Ollama service is not running. Starting now...${NC}"
    
    # Start Ollama in the background
    echo "Starting Ollama service in the background..."
    nohup ollama serve > ollama.log 2>&1 &
    
    # Wait for service to start
    echo "Waiting for Ollama service to start..."
    max_attempts=10
    attempt=1
    while ! curl -s http://localhost:11434/api/tags &> /dev/null; do
        if [ $attempt -ge $max_attempts ]; then
            echo -e "${RED}Failed to start Ollama service after ${max_attempts} attempts.${NC}"
            echo "Please start it manually with 'ollama serve'"
            exit 1
        fi
        echo "Attempt $attempt/$max_attempts. Waiting 2 seconds..."
        sleep 2
        ((attempt++))
    done
    
    echo -e "${GREEN}✓ Ollama service started successfully${NC}"
fi

# Step 3: Check if model is available and pull if needed
echo -e "\n${BLUE}Step 3: Checking if model '$MODEL' is available...${NC}"
if ollama list | grep -q "$MODEL"; then
    echo -e "${GREEN}✓ Model '$MODEL' is already downloaded${NC}"
else
    echo -e "${YELLOW}Model '$MODEL' is not downloaded. Downloading now...${NC}"
    echo "This may take a while depending on your internet connection and the model size."
    echo "Please be patient..."
    
    ollama pull $MODEL
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Model '$MODEL' downloaded successfully${NC}"
    else
        echo -e "${RED}Failed to download model '$MODEL'.${NC}"
        echo "Please download it manually with 'ollama pull $MODEL'"
        exit 1
    fi
fi

# Step 4: Set environment variables
echo -e "\n${BLUE}Step 4: Setting up environment variables...${NC}"
echo "Adding environment variables to your .bashrc file..."

# Check if variables already exist
if grep -q "OLLAMA_MODEL" ~/.bashrc; then
    echo -e "${YELLOW}Environment variables already exist in .bashrc. Skipping.${NC}"
else
    cat >> ~/.bashrc << EOF

# AutoCommit environment variables
export OLLAMA_MODEL="$MODEL"
export OLLAMA_HOST="http://localhost:11434"
export AUTOCOMMIT_TEMP="0.2"
export AUTOCOMMIT_MAX_TOKENS="256"
export AUTOCOMMIT_TIMEOUT="10"
EOF
    echo -e "${GREEN}✓ Environment variables added to .bashrc${NC}"
    echo -e "${YELLOW}Note: You'll need to restart your terminal or run 'source ~/.bashrc' for these to take effect.${NC}"
fi

# Final step: Summary
echo -e "\n${BLUE}=======================================${NC}"
echo -e "${GREEN}✓ Ollama setup completed successfully${NC}"
echo -e "${BLUE}=======================================${NC}"
echo -e "\nSummary:"
echo -e "  - Ollama installed: $(which ollama)"
echo -e "  - Ollama version: $(ollama --version 2>&1)"
echo -e "  - Ollama service: Running"
echo -e "  - Model: $MODEL installed"
echo -e "  - Environment variables: Configured in .bashrc"
echo
echo -e "You can now use AutoCommit with Ollama. If you encounter any issues,"
echo -e "please refer to the docs/OLLAMA_SETUP.md documentation file."
echo
echo -e "${YELLOW}Important: You may need to restart your terminal or run 'source ~/.bashrc'${NC}"
echo -e "${YELLOW}to apply the environment variables.${NC}"
echo
echo -e "${BLUE}Happy committing!${NC}"