#!/bin/bash
# Pi WiFi Monitor - Setup Script
# This script helps you set up the monitoring stack on your Raspberry Pi

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║           Pi WiFi Monitor - Setup Script                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running on Raspberry Pi
check_raspberry_pi() {
    if [ -f /proc/device-tree/model ]; then
        model=$(cat /proc/device-tree/model)
        echo -e "${GREEN}✓ Detected: $model${NC}"
    else
        echo -e "${YELLOW}⚠ Not running on Raspberry Pi (or model not detected)${NC}"
        echo -e "${YELLOW}  This setup should still work on most Linux systems${NC}"
    fi
}

# Check for Docker
check_docker() {
    echo -e "\n${BLUE}Checking Docker installation...${NC}"
    if command -v docker &> /dev/null; then
        docker_version=$(docker --version)
        echo -e "${GREEN}✓ Docker installed: $docker_version${NC}"
    else
        echo -e "${RED}✗ Docker not found${NC}"
        echo -e "${YELLOW}Please install Docker first:${NC}"
        echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
        echo "  sudo sh get-docker.sh"
        echo "  sudo usermod -aG docker \$USER"
        echo "  # Log out and back in for group changes to take effect"
        exit 1
    fi

    if command -v docker-compose &> /dev/null; then
        compose_version=$(docker-compose --version)
        echo -e "${GREEN}✓ Docker Compose installed: $compose_version${NC}"
    elif docker compose version &> /dev/null; then
        compose_version=$(docker compose version)
        echo -e "${GREEN}✓ Docker Compose (plugin) installed: $compose_version${NC}"
    else
        echo -e "${RED}✗ Docker Compose not found${NC}"
        echo -e "${YELLOW}Please install Docker Compose:${NC}"
        echo "  sudo apt-get install docker-compose-plugin"
        exit 1
    fi
}

# Detect network range
detect_network() {
    echo -e "\n${BLUE}Detecting network configuration...${NC}"

    # Get default interface
    default_interface=$(ip route | grep default | awk '{print $5}' | head -n1)

    if [ -n "$default_interface" ]; then
        # Get IP address
        ip_address=$(ip -4 addr show "$default_interface" | grep inet | awk '{print $2}' | head -n1)
        network_range=$(echo "$ip_address" | sed 's/\.[0-9]*\//.0\//')

        echo -e "${GREEN}✓ Default interface: $default_interface${NC}"
        echo -e "${GREEN}✓ IP Address: $ip_address${NC}"
        echo -e "${GREEN}✓ Detected network range: $network_range${NC}"

        DETECTED_NETWORK=$network_range
    else
        echo -e "${YELLOW}⚠ Could not detect network automatically${NC}"
        DETECTED_NETWORK="192.168.1.0/24"
    fi
}

# Create .env file
create_env_file() {
    echo -e "\n${BLUE}Setting up environment configuration...${NC}"

    if [ -f .env ]; then
        echo -e "${YELLOW}⚠ .env file already exists${NC}"
        read -p "  Overwrite? (y/N): " overwrite
        if [[ ! $overwrite =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}  Keeping existing .env file${NC}"
            return
        fi
    fi

    cp .env.example .env

    # Update network range
    if [ -n "$DETECTED_NETWORK" ]; then
        sed -i "s|NETWORK_RANGE=.*|NETWORK_RANGE=$DETECTED_NETWORK|" .env
        echo -e "${GREEN}✓ Set network range to $DETECTED_NETWORK${NC}"
    fi

    echo -e "\n${YELLOW}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}IMPORTANT: Telegram Bot Configuration${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
    echo -e "To receive alerts via Telegram, you need to:"
    echo -e "1. Create a bot with ${BLUE}@BotFather${NC} on Telegram"
    echo -e "   - Send /newbot and follow the instructions"
    echo -e "   - Copy the bot token"
    echo -e ""
    echo -e "2. Get your Chat ID:"
    echo -e "   - Message ${BLUE}@userinfobot${NC} or ${BLUE}@get_id_bot${NC}"
    echo -e "   - Copy your chat ID"
    echo -e ""

    read -p "Do you want to configure Telegram now? (y/N): " configure_telegram

    if [[ $configure_telegram =~ ^[Yy]$ ]]; then
        read -p "Enter your Telegram Bot Token: " bot_token
        read -p "Enter your Telegram Chat ID: " chat_id

        if [ -n "$bot_token" ]; then
            sed -i "s|TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$bot_token|" .env
            echo -e "${GREEN}✓ Bot token configured${NC}"
        fi

        if [ -n "$chat_id" ]; then
            sed -i "s|TELEGRAM_CHAT_ID=.*|TELEGRAM_CHAT_ID=$chat_id|" .env
            # Also update alertmanager config
            sed -i "s|chat_id: 0.*|chat_id: $chat_id|" alertmanager/alertmanager.yml
            echo -e "${GREEN}✓ Chat ID configured${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Skipping Telegram configuration${NC}"
        echo -e "${YELLOW}  You can edit .env and alertmanager/alertmanager.yml later${NC}"
    fi

    echo -e "${GREEN}✓ Environment file created${NC}"
}

# Build and start services
start_services() {
    echo -e "\n${BLUE}Building and starting services...${NC}"

    # Use docker compose (plugin) or docker-compose
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi

    echo -e "${YELLOW}Building Docker images (this may take a few minutes)...${NC}"
    $COMPOSE_CMD build

    echo -e "\n${YELLOW}Starting services...${NC}"
    $COMPOSE_CMD up -d

    echo -e "${GREEN}✓ Services started${NC}"
}

# Show status
show_status() {
    echo -e "\n${BLUE}Checking service status...${NC}"

    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi

    $COMPOSE_CMD ps
}

# Get Pi IP address
get_pi_ip() {
    hostname -I | awk '{print $1}'
}

# Print access information
print_access_info() {
    PI_IP=$(get_pi_ip)

    echo -e "\n${GREEN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║              Setup Complete! 🎉                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo -e "${BLUE}Access your monitoring dashboard:${NC}"
    echo -e "  Grafana:      ${GREEN}http://$PI_IP:3000${NC}"
    echo -e "  Prometheus:   ${GREEN}http://$PI_IP:9090${NC}"
    echo -e "  Alertmanager: ${GREEN}http://$PI_IP:9093${NC}"
    echo ""
    echo -e "${BLUE}Default Grafana credentials:${NC}"
    echo -e "  Username: ${GREEN}admin${NC}"
    echo -e "  Password: ${GREEN}admin${NC}"
    echo ""
    echo -e "${YELLOW}Note: The first speed test will run immediately.${NC}"
    echo -e "${YELLOW}Data will start appearing in Grafana within a few minutes.${NC}"
    echo ""
    echo -e "${BLUE}Useful commands:${NC}"
    echo "  View logs:      docker compose logs -f"
    echo "  Stop services:  docker compose down"
    echo "  Restart:        docker compose restart"
    echo ""
}

# Main execution
main() {
    check_raspberry_pi
    check_docker
    detect_network
    create_env_file
    start_services
    show_status
    print_access_info
}

# Run main function
main
