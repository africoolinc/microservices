#!/bin/bash
# Gibson's Stack Manager - Master Control Script
# Provides menu-driven management of the remote microservices stack

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config/remote_config.txt"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Load config
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    REMOTE_HOST="10.144.118.159"
    REMOTE_USER="gibz"
    REMOTE_PASS="Lamborghini"
fi

show_header() {
    clear
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}    GIBSON'S STACK MANAGER v1.0${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo -e "${YELLOW}Remote:${NC} $REMOTE_USER@$REMOTE_HOST"
    echo -e "${YELLOW}Time:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

show_menu() {
    echo -e "${GREEN}MAIN MENU${NC}"
    echo "----------------------------------------"
    echo "1) 🔍 Check Services Health"
    echo "2) 📦 Backup Stack"
    echo "3) 🔐 Setup SSH Access"
    echo "4) 📤 Setup GitHub Repository"
    echo "5) 🌐 Update Remote IP"
    echo "6) ☁️  Deploy to Cloud"
    echo "7) 📋 View GitHub SSH Key"
    echo "8) 📖 Open Documentation"
    echo ""
    echo "9) 🚀 Quick Connect (SSH)"
    echo "0) ❌ Exit"
    echo ""
    echo -n "Select option: "
}

check_services() {
    echo -e "${BLUE}Checking all services...${NC}"
    "$SCRIPT_DIR/check_services.sh"
    echo ""
    read -p "Press Enter to continue..."
}

backup_stack() {
    echo -e "${BLUE}Creating backup...${NC}"
    "$SCRIPT_DIR/backup_stack.sh"
    echo ""
    read -p "Press Enter to continue..."
}

setup_ssh() {
    echo -e "${BLUE}Setting up SSH access...${NC}"
    "$SCRIPT_DIR/setup_ssh.sh" "$REMOTE_HOST" "$REMOTE_USER" "$REMOTE_PASS"
    echo ""
    read -p "Press Enter to continue..."
}

setup_github() {
    echo -e "${BLUE}Setting up GitHub repository...${NC}"
    echo ""
    echo -e "${YELLOW}SSH Public Key (add to https://github.com/settings/keys):${NC}"
    cat "$SCRIPT_DIR/../ssh/github_ssh_key.pub"
    echo ""
    read -p "Press Enter after adding key to GitHub..."
    echo ""
    "$SCRIPT_DIR/setup_github_repo.sh"
    echo ""
    read -p "Press Enter to continue..."
}

update_ip() {
    echo -n "Enter new IP address: "
    read new_ip
    if [ -n "$new_ip" ]; then
        "$SCRIPT_DIR/update_remote_ip.sh" "$new_ip"
        # Reload config
        source "$CONFIG_FILE"
    fi
    echo ""
    read -p "Press Enter to continue..."
}

deploy_cloud() {
    echo -e "${BLUE}Cloud deployment options...${NC}"
    "$SCRIPT_DIR/deploy-cloud.sh" --help
    echo ""
    read -p "Press Enter to continue..."
}

show_ssh_key() {
    echo -e "${YELLOW}GitHub SSH Public Key:${NC}"
    echo "----------------------------------------"
    cat "$SCRIPT_DIR/../ssh/github_ssh_key.pub"
    echo ""
    echo -e "${CYAN}Add to:${NC} https://github.com/settings/keys"
    echo ""
    read -p "Press Enter to continue..."
}

open_docs() {
    echo -e "${BLUE}Documentation files:${NC}"
    echo "----------------------------------------"
    ls -1 "$SCRIPT_DIR/../docs/"
    echo ""
    echo "Enter filename to view (or Enter to skip):"
    read docfile
    if [ -n "$docfile" ] && [ -f "$SCRIPT_DIR/../docs/$docfile" ]; then
        less "$SCRIPT_DIR/../docs/$docfile"
    fi
    echo ""
    read -p "Press Enter to continue..."
}

quick_connect() {
    echo -e "${GREEN}Connecting to remote machine...${NC}"
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$REMOTE_USER@$REMOTE_HOST" || {
        echo -e "${RED}Connection failed. Try:${NC}"
        echo "  1. Check if IP is correct"
        echo "  2. Run option 5 to update IP"
        echo "  3. Run option 3 to setup SSH"
    }
    echo ""
    read -p "Press Enter to continue..."
}

# Main loop
while true; do
    show_header
    show_menu
    read choice

    case $choice in
        1) check_services ;;
        2) backup_stack ;;
        3) setup_ssh ;;
        4) setup_github ;;
        5) update_ip ;;
        6) deploy_cloud ;;
        7) show_ssh_key ;;
        8) open_docs ;;
        9) quick_connect ;;
        0) echo -e "${GREEN}Goodbye!${NC}"; exit 0 ;;
        *) echo -e "${RED}Invalid option${NC}"; sleep 1 ;;
    esac
done
