#!/bin/bash
# Development installation script for Committy

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}Committy - Development Setup Script${NC}"
echo -e "${BLUE}=======================================${NC}\n"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment.${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -e .
pip install -r requirements-dev.txt

# Check if Ollama is installed
echo -e "${YELLOW}Checking for Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}Ollama not found. You will need to install it manually.${NC}"
    echo -e "See docs/OLLAMA_SETUP.md for installation instructions."
else
    echo -e "${GREEN}Ollama is installed.${NC}"
fi

# Create symlink for the CLI
echo -e "${YELLOW}Creating CLI symlink...${NC}"
chmod +x scripts/committy
mkdir -p ~/.local/bin

# Check if symlink already exists
if [ -L ~/.local/bin/committy ]; then
    echo -e "${YELLOW}Symlink already exists. Removing...${NC}"
    rm ~/.local/bin/committy
fi

# Create new symlink
ln -s "$(pwd)/scripts/committy" ~/.local/bin/committy
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create symlink. You may need to create it manually.${NC}"
else
    echo -e "${GREEN}Symlink created at ~/.local/bin/committy${NC}"
fi

# Set up bash completion
echo -e "${YELLOW}Setting up bash completion...${NC}"
mkdir -p ~/.bash_completion.d
cp scripts/completions/committy.bash ~/.bash_completion.d/committy
echo -e "${GREEN}Bash completion installed to ~/.bash_completion.d/committy${NC}"
echo -e "${YELLOW}Add the following line to your ~/.bashrc:${NC}"
echo -e "source ~/.bash_completion.d/committy"

# Create default config
echo -e "${YELLOW}Creating default configuration...${NC}"
mkdir -p ~/.config/committy
python -m committy --init-config

echo -e "\n${GREEN}=======================================${NC}"
echo -e "${GREEN}Committy development setup complete!${NC}"
echo -e "${GREEN}=======================================${NC}\n"

echo -e "To use Committy:"
echo -e "1. ${YELLOW}~/.local/bin/committy${NC} (or just ${YELLOW}committy${NC} if ~/.local/bin is in your PATH)"
echo -e "2. Update your PATH if needed: ${YELLOW}export PATH=\$PATH:~/.local/bin${NC}"
echo -e "3. To deactivate the virtual environment: ${YELLOW}deactivate${NC}"

echo -e "\n${BLUE}Happy committing!${NC}"