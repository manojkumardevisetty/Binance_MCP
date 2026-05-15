#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}"
echo "🚀 Binance Futures MCP Server - Automated Setup"
echo "================================================${NC}"
echo ""

# Check if running as ubuntu user
if [ "$USER" != "ubuntu" ]; then
    echo -e "${RED}❌ Please run as ubuntu user (not root)${NC}"
    exit 1
fi

# Step 1: Update system
echo -e "${YELLOW}Step 1: Updating system...${NC}"
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git build-essential htop tmux nano openssl

# Step 2: Install Python
echo -e "${YELLOW}Step 2: Installing Python 3.12...${NC}"
sudo apt install -y python3.12 python3.12-venv python3-pip

# Step 3: Install Node.js
echo -e "${YELLOW}Step 3: Installing Node.js...${NC}"
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Step 4: Install PM2 & NGINX
echo -e "${YELLOW}Step 4: Installing PM2 & NGINX...${NC}"
sudo npm install -g pm2
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Step 5: Create directories
echo -e "${YELLOW}Step 5: Creating application directories...${NC}"
sudo mkdir -p /opt/binance-mcp/{src,data,logs}
sudo chown ubuntu:ubuntu /opt/binance-mcp

# Step 6: Setup Python venv
echo -e "${YELLOW}Step 6: Setting up Python virtual environment...${NC}"
cd /opt/binance-mcp
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn pyjwt python-binance requests python-dotenv

# Step 7: Generate JWT secret
echo -e "${YELLOW}Step 7: Generating JWT secret...${NC}"
JWT_SECRET=$(openssl rand -hex 32)

# Step 8: Create ecosystem.config.js
echo -e "${YELLOW}Step 8: Creating PM2 configuration...${NC}"
sudo tee /opt/binance-mcp/ecosystem.config.js > /dev/null << EOF
module.exports = {
  apps: [{
    name: "binance-mcp",
    script: "/opt/binance-mcp/venv/bin/python",
    args: "/opt/binance-mcp/src/server_http.py",
    cwd: "/opt/binance-mcp",
    env: {
      JWT_SECRET: "$JWT_SECRET",
      BINANCE_TESTNET: "false",
      DRY_RUN: "false",
      MAX_LEVERAGE: "100",
      MAX_NOTIONAL_USDT: "50000",
      DAILY_LOSS_LIMIT_USDT: "20000",
      SYMBOL_WHITELIST: "BTCUSDT,ETHUSDT,SOLUSDT,AVAXUSDT,XRPUSDT,DOGEUSDT",
      PORT: "8765",
      HOST: "127.0.0.1"
    },
    log_file: "/opt/binance-mcp/logs/combined.log",
    error_file: "/opt/binance-mcp/logs/error.log",
    out_file: "/opt/binance-mcp/logs/out.log",
    time: true,
    restart_delay: 5000,
    max_restarts: 10
  }]
}
EOF

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Copy server_http.py to /opt/binance-mcp/src/"
echo "2. Copy manage_users.sh to /opt/binance-mcp/"
echo "3. Configure NGINX with your domain"
echo "4. Run: sudo pm2 start /opt/binance-mcp/ecosystem.config.js"
echo "5. Add users: sudo /opt/binance-mcp/manage_users.sh add <username> <key> <secret>"
echo ""
echo -e "${GREEN}JWT_SECRET: $JWT_SECRET${NC}"
echo ""
