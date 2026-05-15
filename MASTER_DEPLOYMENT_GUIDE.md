# Binance Futures MCP Server - MASTER DEPLOYMENT GUIDE
## Complete Step-by-Step with All Commands & Files

---

## 📌 TABLE OF CONTENTS

1. [What You're Getting](#what-youre-getting)
2. [System Requirements](#system-requirements)
3. [File Structure](#file-structure)
4. [Installation Steps](#installation-steps)
5. [User Management](#user-management)
6. [Server Management](#server-management)
7. [Windows Claude Setup](#windows-claude-setup)
8. [Configuration Reference](#configuration-reference)
9. [Troubleshooting](#troubleshooting)
10. [Security Checklist](#security-checklist)

---

## 📦 What You're Getting

### Core Files (Copy These to VPS)
```
server_http_ADVANCED.py      → /opt/binance-mcp/src/server_http.py
manage_users.sh              → /opt/binance-mcp/manage_users.sh
ecosystem.config.js          → /opt/binance-mcp/ecosystem.config.js
nginx-binance-mcp.conf       → /etc/nginx/sites-available/binance-mcp
requirements.txt             → /opt/binance-mcp/requirements.txt
setup.sh                     → Run on VPS
restart.sh                   → /opt/binance-mcp/restart.sh
```

### Features
✅ All Binance Futures trading tools (20+ commands)
✅ Multi-user with JWT authentication
✅ 24/7 uptime with PM2
✅ HTTPS/SSL with NGINX
✅ User management (add/delete/list)
✅ Risk limits (leverage, notional, daily loss)
✅ 1000+ trading pairs supported
✅ Windows Claude Desktop integration

---

## 🖥️ System Requirements

### VPS Specs (Minimum)
- **OS:** Ubuntu 24.04 LTS
- **RAM:** 2GB minimum (4GB recommended)
- **CPU:** 2 cores minimum
- **Storage:** 20GB
- **Network:** Public IP with domain

### What Gets Installed
- Python 3.12 + venv
- Node.js 18+
- PM2 (process manager)
- NGINX (reverse proxy)
- Certbot (SSL certificates)
- python-binance, FastAPI, Uvicorn

---

## 📁 File Structure (After Deployment)

```
/opt/binance-mcp/                    ← Main application directory
├── src/
│   └── server_http.py               ← Main MCP server (CRITICAL)
├── manage_users.sh                  ← User management script
├── ecosystem.config.js              ← PM2 configuration
├── requirements.txt                 ← Python dependencies
├── restart.sh                       ← Restart script
├── venv/                            ← Python virtual environment
│   └── bin/python
├── data/
│   └── users.json                   ← User credentials (BACKUP!)
└── logs/
    ├── combined.log
    ├── error.log
    └── out.log

/etc/nginx/sites-available/
└── binance-mcp                      ← NGINX config

/etc/letsencrypt/live/
└── your-domain.com/                 ← SSL certificates
```

---

## 🚀 INSTALLATION STEPS (30 minutes)

### STEP 0: Preparation (On Your Computer)

1. **Download all files** from `/mnt/user-data/outputs/`
2. **Have ready:**
   - Ubuntu 24.04 VPS IP address
   - Domain name (with DNS configured)
   - Binance Futures API key
   - Binance Futures API secret

### STEP 1: SSH to VPS (2 minutes)

```bash
# Connect to VPS
ssh ubuntu@your_vps_ip

# Example:
# ssh ubuntu@51.222.156.43

# Update system
sudo apt update && sudo apt upgrade -y

# Install basic tools
sudo apt install -y curl wget git nano htop tmux
```

### STEP 2: Run Automated Setup (3 minutes)

**Option A: Using setup.sh (Automated)**

```bash
# Download and run setup script
cd /tmp
wget https://raw.githubusercontent.com/your-repo/setup.sh
# OR create it locally:
cat > setup.sh << 'EOF'
#!/bin/bash
set -e
echo "🚀 Installing dependencies..."
sudo apt install -y python3.12 python3.12-venv python3-pip nodejs npm
sudo npm install -g pm2
sudo apt install -y nginx certbot python3-certbot-nginx

echo "📁 Creating directories..."
sudo mkdir -p /opt/binance-mcp/{src,data,logs}
sudo chown ubuntu:ubuntu /opt/binance-mcp

cd /opt/binance-mcp
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn pyjwt python-binance requests

echo "✅ Setup complete!"
EOF

bash setup.sh
```

**Option B: Manual Setup (If setup.sh fails)**

```bash
# Python 3.12
sudo apt install -y python3.12 python3.12-venv python3-pip

# Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# PM2
sudo npm install -g pm2

# NGINX & Certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# Enable services
sudo systemctl enable nginx
sudo systemctl start nginx

# Create directories
sudo mkdir -p /opt/binance-mcp/{src,data,logs}
sudo chown ubuntu:ubuntu /opt/binance-mcp

# Python venv
cd /opt/binance-mcp
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn pyjwt python-binance requests
```

### STEP 3: Copy Application Files (2 minutes)

**Copy from your computer to VPS:**

```bash
# Copy all files from your outputs folder to VPS
scp server_http_ADVANCED.py ubuntu@your_vps_ip:/tmp/
scp manage_users.sh ubuntu@your_vps_ip:/tmp/
scp ecosystem.config.js ubuntu@your_vps_ip:/tmp/
scp nginx-binance-mcp.conf ubuntu@your_vps_ip:/tmp/
scp requirements.txt ubuntu@your_vps_ip:/tmp/
scp restart.sh ubuntu@your_vps_ip:/tmp/
```

**Or create them directly on VPS:**

```bash
# On VPS, paste the server_http_ADVANCED.py content:
sudo tee /opt/binance-mcp/src/server_http.py > /dev/null << 'EOF'
[PASTE server_http_ADVANCED.py CONTENT HERE]
EOF

# Paste manage_users.sh content:
sudo tee /opt/binance-mcp/manage_users.sh > /dev/null << 'EOF'
[PASTE manage_users.sh CONTENT HERE]
EOF
sudo chmod +x /opt/binance-mcp/manage_users.sh

# Copy other files
cp /tmp/ecosystem.config.js /opt/binance-mcp/
cp /tmp/requirements.txt /opt/binance-mcp/
cp /tmp/restart.sh /opt/binance-mcp/
chmod +x /opt/binance-mcp/restart.sh
```

### STEP 4: Edit Configuration (3 minutes)

```bash
# Edit ecosystem.config.js
nano /opt/binance-mcp/ecosystem.config.js

# MUST CHANGE:
# 1. Line: JWT_SECRET: "40bdbe..." → Generate new: openssl rand -hex 32
# 2. BINANCE_TESTNET: "false" (for mainnet) or "true" (for testnet)
# 3. MAX_LEVERAGE: "100" (or your preference: "5", "10", etc)
# 4. SYMBOL_WHITELIST: Add/remove symbols as needed

# After editing, save with Ctrl+X, Y, Enter
```

**Example ecosystem.config.js:**

```javascript
module.exports = {
  apps: [{
    name: "binance-mcp",
    script: "/opt/binance-mcp/venv/bin/python",
    args: "/opt/binance-mcp/src/server_http.py",
    cwd: "/opt/binance-mcp",
    env: {
      JWT_SECRET: "40bdbe0528ac11864ff73defc5913ec7a44b0324530fdd752b98e5c64fcaf688",
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
```

### STEP 5: Configure NGINX (3 minutes)

```bash
# Copy NGINX config
sudo cp /tmp/nginx-binance-mcp.conf /etc/nginx/sites-available/binance-mcp

# Edit for your domain
sudo nano /etc/nginx/sites-available/binance-mcp

# MUST CHANGE:
# Replace: binance.globalhostia.com → your-domain.com (appears 3 times)

# Enable site
sudo ln -sf /etc/nginx/sites-available/binance-mcp /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Reload
sudo systemctl reload nginx
```

**Example NGINX config (after edits):**

```nginx
server {
    server_name your-domain.com;
    
    location /messages {
        proxy_pass         http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   Authorization $http_authorization;
        proxy_buffering    off;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:8765;
    }
    
    location / { return 404; }
    
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### STEP 6: Get SSL Certificate (5 minutes)

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate (REPLACE your-domain.com)
sudo certbot certonly --nginx -d your-domain.com

# Enable auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Verify cert was created
ls -la /etc/letsencrypt/live/your-domain.com/
```

### STEP 7: Start Server (2 minutes)

```bash
# Activate venv
cd /opt/binance-mcp
source venv/bin/activate

# Test server manually (Ctrl+C to stop)
python3 src/server_http.py
# Should show: "Starting on 127.0.0.1:8765"

# Start with PM2
sudo pm2 start ecosystem.config.js

# Check status
sudo pm2 status

# View logs
sudo pm2 logs binance-mcp --lines 20
```

### STEP 8: Enable PM2 Startup (2 minutes)

```bash
# Save PM2
sudo pm2 save

# Enable startup on reboot
sudo pm2 startup systemd -u ubuntu --hp /home/ubuntu

# Verify (should show "ubuntu" user)
sudo systemctl status pm2-ubuntu

# Check will auto-start after reboot
sudo pm2 list
```

### STEP 9: Add First User (2 minutes)

```bash
# Add your trading account
sudo /opt/binance-mcp/manage_users.sh add customer_manoj YOUR_BINANCE_API_KEY YOUR_BINANCE_API_SECRET

# Example:
# sudo /opt/binance-mcp/manage_users.sh add customer_manoj ABC123XYZ789... XYZ789ABC123...

# Verify user was created
sudo /opt/binance-mcp/manage_users.sh list

# View users database
cat /opt/binance-mcp/data/users.json
```

### STEP 10: Get JWT Token (1 minute)

```bash
# Get token for your user
sudo /opt/binance-mcp/manage_users.sh token customer_manoj

# Output will show:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# User: customer_manoj
# Token: eyJ0eXAiOiJKV1QiLC...
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MCP Server URL:  https://your-domain.com/messages
# JWT Token:       eyJ0eXAiOiJKV1QiLC...

# COPY THIS TOKEN - you'll need it for Windows
```

### STEP 11: Test Server (2 minutes)

```bash
# Test health endpoint
curl -s https://your-domain.com/health

# Should return: {"status": "ok"}

# Test with token (replace with your token)
curl -X POST https://your-domain.com/messages \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_account_info",
      "arguments": {}
    }
  }'

# Should return account info
```

---

## 👥 USER MANAGEMENT

### Add User

```bash
sudo /opt/binance-mcp/manage_users.sh add <username> <api_key> <api_secret>

# Examples:
sudo /opt/binance-mcp/manage_users.sh add customer_manoj ABC123KEY XYZ789SECRET
sudo /opt/binance-mcp/manage_users.sh add customer_john DEF456KEY UVW012SECRET
sudo /opt/binance-mcp/manage_users.sh add customer_jane GHI789KEY RST345SECRET
```

### List All Users

```bash
sudo /opt/binance-mcp/manage_users.sh list

# Output:
# 📋 Registered Users:
# ====================
#   • customer_manoj
#   • customer_john
#   • customer_jane
```

### Get JWT Token

```bash
sudo /opt/binance-mcp/manage_users.sh token <username>

# Example:
sudo /opt/binance-mcp/manage_users.sh token customer_manoj

# Output will show token and setup instructions
```

### Delete User

```bash
sudo /opt/binance-mcp/manage_users.sh delete <username>

# Example:
sudo /opt/binance-mcp/manage_users.sh delete customer_john

# Confirm: ✅ User customer_john deleted
```

### View Users Database

```bash
# See all users with metadata
cat /opt/binance-mcp/data/users.json

# Example output:
# {
#   "customer_manoj": {
#     "binance_api_key": "ABC123...",
#     "binance_api_secret": "XYZ789...",
#     "created": "2026-05-14T07:20:49.096955Z"
#   },
#   "customer_john": {
#     "binance_api_key": "DEF456...",
#     "binance_api_secret": "UVW012...",
#     "created": "2026-05-15T08:04:49.431196Z"
#   }
# }
```

---

## 🔧 SERVER MANAGEMENT

### Start Server

```bash
sudo pm2 start /opt/binance-mcp/ecosystem.config.js

# Or use existing app
sudo pm2 start binance-mcp
```

### Stop Server

```bash
sudo pm2 stop binance-mcp
```

### Restart Server

```bash
# Soft restart (keeps environment)
sudo pm2 restart binance-mcp

# Hard restart (full reload)
sudo pm2 delete binance-mcp
sudo pm2 start /opt/binance-mcp/ecosystem.config.js
```

### View Logs

```bash
# Real-time logs
sudo pm2 logs binance-mcp

# Last 50 lines
sudo pm2 logs binance-mcp --lines 50

# Error logs only
sudo tail -f /opt/binance-mcp/logs/error.log

# Combined logs
sudo tail -f /opt/binance-mcp/logs/combined.log
```

### Monitor Performance

```bash
# CPU & Memory usage
sudo pm2 monit

# Server status
sudo pm2 status

# Detailed info
sudo pm2 info binance-mcp
```

### View Server Health

```bash
# Check health endpoint
curl -s https://your-domain.com/health

# Check if port is open
sudo netstat -tlnp | grep 8765

# Check NGINX
sudo systemctl status nginx
```

### Using Restart Script

```bash
# Built-in restart script (easier)
sudo bash /opt/binance-mcp/restart.sh

# This does:
# 1. Stops PM2
# 2. Waits 1 second
# 3. Starts fresh
# 4. Shows status & logs
```

---

## 🪟 WINDOWS CLAUDE SETUP

### Step 1: Get JWT Token

```bash
# On VPS, get token
sudo /opt/binance-mcp/manage_users.sh token customer_manoj

# Copy the token (long string starting with eyJ...)
```

### Step 2: Create Batch File

**On Windows, create `C:\binance-mcp.bat`:**

```batch
@echo off
"C:\Program Files\nodejs\npx.cmd" -y mcp-remote "https://your-domain.com/messages" --header "Authorization:Bearer eyJ0eXAiOiJKV1QiLC..." 
```

Replace:
- `your-domain.com` with your actual domain
- `eyJ0eXAiOiJKV1QiLC...` with your actual JWT token

### Step 3: Update Claude Config

**Edit `%APPDATA%\Claude\claude_desktop_config.json`:**

```json
{
  "mcpServers": {
    "binance-futures": {
      "command": "C:\\binance-mcp.bat",
      "args": []
    }
  }
}
```

### Step 4: Restart Claude Desktop

1. **Fully quit Claude:**
   - System Tray → Right-click Claude → Quit
   - Or: Alt+F4 multiple times
   - **Check Task Manager** - make sure Claude process is gone

2. **Reopen Claude Desktop**

3. **Test it works:**
   - Ask: "Get account info"
   - Ask: "Get mark price BTCUSDT"
   - Ask: "Place market order BTCUSDT BUY 0.01 5x"

---

## ⚙️ CONFIGURATION REFERENCE

### ecosystem.config.js Variables

```javascript
env: {
  // SECURITY - MUST CHANGE!
  JWT_SECRET: "40bdbe...",           // Generate: openssl rand -hex 32
  
  // TRADING MODE
  BINANCE_TESTNET: "false",           // false=mainnet, true=testnet
  DRY_RUN: "false",                   // false=live, true=simulation
  
  // RISK LIMITS
  MAX_LEVERAGE: "100",                // Maximum leverage allowed (1-100)
  MAX_NOTIONAL_USDT: "50000",         // Max order size per trade
  DAILY_LOSS_LIMIT_USDT: "20000",     // Daily loss circuit breaker
  
  // ALLOWED SYMBOLS
  SYMBOL_WHITELIST: "BTCUSDT,ETHUSDT,SOLUSDT,AVAXUSDT",
  // Or leave empty for all symbols
  
  // SERVER
  PORT: "8765",                       // Internal port
  HOST: "127.0.0.1"                   // Bind address
}
```

### Generate New JWT Secret

```bash
# Generate 64-character random hex string
openssl rand -hex 32

# Output: 40bdbe0528ac11864ff73defc5913ec7a44b0324530fdd752b98e5c64fcaf688

# Replace in ecosystem.config.js and restart
```

### Quick Config Changes

```bash
# Switch to testnet
sudo sed -i 's/BINANCE_TESTNET: "false"/BINANCE_TESTNET: "true"/' /opt/binance-mcp/ecosystem.config.js

# Change max leverage to 5x
sudo sed -i 's/MAX_LEVERAGE: "100"/MAX_LEVERAGE: "5"/' /opt/binance-mcp/ecosystem.config.js

# Restart to apply
sudo pm2 restart binance-mcp
```

---

## 🆘 TROUBLESHOOTING

### Server Won't Start

```bash
# Check logs
sudo pm2 logs binance-mcp --lines 100

# Test Python directly
source /opt/binance-mcp/venv/bin/activate
python3 /opt/binance-mcp/src/server_http.py

# Check port in use
sudo lsof -i :8765

# Check if venv is correct
ls -la /opt/binance-mcp/venv/bin/python3
```

### "API Key Invalid" Error

```bash
# Verify users.json
cat /opt/binance-mcp/data/users.json

# Test API directly
source /opt/binance-mcp/venv/bin/activate
python3 << 'EOF'
from binance.client import Client

api_key = "YOUR_KEY"
api_secret = "YOUR_SECRET"

try:
    client = Client(api_key, api_secret, testnet=False)
    account = client.futures_account()
    print(f"✅ API works! Balance: {account.get('totalWalletBalance')}")
except Exception as e:
    print(f"❌ Error: {str(e)}")
EOF
```

### NGINX Connection Refused

```bash
# Check NGINX status
sudo systemctl status nginx

# Check if listening
sudo netstat -tlnp | grep nginx

# Check config
sudo nginx -t

# Restart NGINX
sudo systemctl restart nginx

# Test endpoint
curl -s https://your-domain.com/health
```

### Claude Can't Connect

```bash
# Verify token is correct
sudo /opt/binance-mcp/manage_users.sh token customer_manoj

# Verify URL works
curl -s -H "Authorization: Bearer YOUR_TOKEN" https://your-domain.com/messages

# Make sure Claude is fully restarted
# Check Task Manager - no claude.exe running
# Delete old config: del %APPDATA%\Claude\claude_desktop_config.json.bak

# Recreate batch file with correct token
# Recreate config.json
# Restart Claude from clean state
```

### High CPU/Memory Usage

```bash
# Monitor in real-time
sudo pm2 monit

# Kill and restart
sudo pm2 delete binance-mcp
sleep 2
sudo pm2 start /opt/binance-mcp/ecosystem.config.js

# Check logs for errors
sudo pm2 logs binance-mcp --lines 50
```

### SSL Certificate Issues

```bash
# Check certificate
sudo certbot certificates

# Renew manually
sudo certbot renew --force-renewal

# Check NGINX can see cert
ls -la /etc/letsencrypt/live/your-domain.com/

# Test HTTPS
curl -v https://your-domain.com/health
```

---

## 🔒 SECURITY CHECKLIST

### Before Going Live

```bash
# 1️⃣ Generate new JWT_SECRET
NEW_SECRET=$(openssl rand -hex 32)
echo $NEW_SECRET
# Copy this and update ecosystem.config.js

# 2️⃣ Get your VPS IP
curl -s https://api.ipify.org
# Output: 51.222.156.43 (for example)

# 3️⃣ Whitelist IP in Binance
# Go to: https://www.binance.com/en/account/api-management
# Click: Edit Restrictions
# IP Whitelist: Paste your VPS IP above

# 4️⃣ Verify SSL works
curl -s https://your-domain.com/health

# 5️⃣ Backup users database
sudo cp /opt/binance-mcp/data/users.json /opt/binance-mcp/data/users.json.backup

# 6️⃣ Set file permissions
sudo chmod 600 /opt/binance-mcp/data/users.json
sudo chmod 600 /opt/binance-mcp/data/users.json.backup

# 7️⃣ Monitor logs
sudo pm2 logs binance-mcp --lines 10

# 8️⃣ Test on testnet first
# Edit ecosystem.config.js: BINANCE_TESTNET: "true"
# Trade on testnet for 24 hours
# Then: BINANCE_TESTNET: "false"

# 9️⃣ Enable PM2 to start on reboot
sudo pm2 save
sudo pm2 startup systemd -u ubuntu --hp /home/ubuntu

# 🔟 Update dependencies monthly
source /opt/binance-mcp/venv/bin/activate
pip install --upgrade python-binance fastapi uvicorn pyjwt
```

---

## 📊 Trading Tools Available

### Account Info
- `get_account_info` - Balance, positions, leverage
- `get_available_symbols` - All trading pairs (1000+)

### Prices & Market Data
- `get_mark_price` - Current price
- `get_24h_stats` - Volume, high, low, change %
- `get_funding_rate` - Perpetual funding rate

### Orders
- `get_open_orders` - List active orders
- `get_order_history` - Past trades

### Positions
- `get_position_leverage` - Current leverage
- `get_position_pnl` - Unrealized P&L
- `get_liquidation_price` - Liquidation level

### Trading (Execution)
- `place_market_order` - Market order
- `place_limit_order` - Limit order
- `place_stop_loss` - Stop loss
- `place_take_profit` - Take profit
- `place_trailing_stop` - Trailing stop
- `modify_order` - Edit order
- `cancel_order` - Cancel order
- `batch_orders` - Multiple orders
- `close_position` - Close all

### Configuration
- `set_leverage` - Change position leverage
- `get_safety_status` - Check limits

---

## ✅ COMPLETE CHECKLIST

- [ ] VPS: Ubuntu 24.04 LTS ready
- [ ] Domain: DNS pointing to VPS
- [ ] Downloaded: All files from outputs
- [ ] SSH: Connected to VPS
- [ ] System: Ran setup.sh
- [ ] Files: Copied all to correct locations
- [ ] Config: Edited ecosystem.config.js (JWT_SECRET, domain)
- [ ] Config: Edited NGINX config (domain name)
- [ ] NGINX: Config tested with `nginx -t`
- [ ] SSL: Certificate created with certbot
- [ ] PM2: Server started with `pm2 start`
- [ ] User: Added first user with manage_users.sh
- [ ] Token: Got JWT token
- [ ] Test: Health check passed (`curl https://your-domain.com/health`)
- [ ] Windows: Created batch file
- [ ] Windows: Updated Claude config
- [ ] Windows: Tested "Get account info"
- [ ] Security: Changed JWT_SECRET
- [ ] Security: Whitelisted VPS IP in Binance
- [ ] Backup: Backed up users.json
- [ ] Monitor: Checked logs (no errors)

---

## 🎯 QUICK REFERENCE (Commands You'll Use)

```bash
# Add user
sudo /opt/binance-mcp/manage_users.sh add customer_name KEY SECRET

# Get token
sudo /opt/binance-mcp/manage_users.sh token customer_name

# List users
sudo /opt/binance-mcp/manage_users.sh list

# Delete user
sudo /opt/binance-mcp/manage_users.sh delete customer_name

# Restart server
sudo pm2 restart binance-mcp

# View logs
sudo pm2 logs binance-mcp --lines 50

# Check status
sudo pm2 status

# Monitor
sudo pm2 monit

# Stop server
sudo pm2 stop binance-mcp

# Start server
sudo pm2 start /opt/binance-mcp/ecosystem.config.js

# Edit config
sudo nano /opt/binance-mcp/ecosystem.config.js

# View users database
cat /opt/binance-mcp/data/users.json

# Test health
curl https://your-domain.com/health

# View error logs
sudo tail -f /opt/binance-mcp/logs/error.log
```

---

## 📞 SUPPORT

Having issues?

1. **Check logs:** `sudo pm2 logs binance-mcp --lines 100`
2. **Verify files:** `ls -la /opt/binance-mcp/`
3. **Test server:** `curl https://your-domain.com/health`
4. **Restart:** `sudo pm2 restart binance-mcp`
5. **Read troubleshooting section above**

---

## 🎉 YOU'RE READY!

You now have:
✅ Production-ready MCP server
✅ Multi-user support
✅ 24/7 uptime
✅ Security hardened
✅ All trading features
✅ Windows integration
✅ Complete documentation

**Deploy it now and start trading!** 🚀

---

**Created:** May 15, 2026
**Updated:** May 15, 2026
**Status:** Production Ready ✅
