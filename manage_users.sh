#!/bin/bash

################################################################################
# Binance MCP SaaS - User Management Script
# Manages customer credentials and JWT tokens
#
# Usage:
#   sudo ./manage_users.sh add <username> <api_key> <api_secret>
#   sudo ./manage_users.sh remove <username>
#   sudo ./manage_users.sh list
#   sudo ./manage_users.sh token <username>
#   sudo ./manage_users.sh info <username>
#   sudo ./manage_users.sh setup <username>
#
# Examples:
#   sudo ./manage_users.sh add customer_manoj KEY SECRET
#   sudo ./manage_users.sh token customer_manoj
#   sudo ./manage_users.sh list
#   sudo ./manage_users.sh setup customer_manoj
#
################################################################################

set -e

# Configuration
USERS_DB="/opt/binance-mcp/data/users.json"
JWT_SECRET="40bdbe0528ac11864ff73defc5913ec7a44b0324530fdd752b98e5c64fcaf688"
DOMAIN="binance.globalhostia.com"
SETUP_DIR="/tmp/binance-mcp-clients"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Functions
show_banner() {
    echo ""
    echo -e "${MAGENTA}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║     Binance MCP SaaS - User Management                      ║${NC}"
    echo -e "${MAGENTA}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

show_usage() {
    cat << EOF
${CYAN}Usage:${NC}
  sudo ./manage_users.sh add <username> <api_key> <api_secret>
  sudo ./manage_users.sh remove <username>
  sudo ./manage_users.sh list
  sudo ./manage_users.sh token <username>
  sudo ./manage_users.sh info <username>
  sudo ./manage_users.sh setup <username>

${CYAN}Examples:${NC}
  sudo ./manage_users.sh add customer_manoj KEY123 SECRET456
  sudo ./manage_users.sh token customer_manoj
  sudo ./manage_users.sh list
  sudo ./manage_users.sh setup customer_manoj
  sudo ./manage_users.sh remove customer_manoj

${CYAN}Commands:${NC}
  add <username> <key> <secret>  - Add new customer with Binance credentials
  remove <username>              - Delete customer
  list                           - List all customers
  token <username>               - Generate JWT token for customer
  info <username>                - Show customer details
  setup <username>               - Generate complete setup files

EOF
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}❌ This script must be run with sudo${NC}"
        exit 1
    fi
}

check_db() {
    if [ ! -f "$USERS_DB" ]; then
        echo -e "${RED}❌ Database not found: $USERS_DB${NC}"
        exit 1
    fi
}

# Add user
add_user() {
    local username="$1"
    local api_key="$2"
    local api_secret="$3"
    
    if [ -z "$username" ] || [ -z "$api_key" ] || [ -z "$api_secret" ]; then
        echo -e "${RED}❌ Missing arguments: username, api_key, api_secret${NC}"
        show_usage
        exit 1
    fi
    
    check_db
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}ADD USER${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Check if user already exists
    if jq -e ".$username" "$USERS_DB" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ User already exists. Updating...${NC}"
    else
        echo -e "${GREEN}✓ Adding new user${NC}"
    fi
    
    # Update JSON
    jq --arg user "$username" \
       --arg key "$api_key" \
       --arg secret "$api_secret" \
       '.[$user] = {
           "binance_api_key": $key,
           "binance_api_secret": $secret,
           "created": now | strftime("%Y-%m-%dT%H:%M:%SZ")
       }' "$USERS_DB" > "$USERS_DB.tmp" && mv "$USERS_DB.tmp" "$USERS_DB"
    
    echo -e "${GREEN}✓ User saved to database${NC}"
    echo ""
    
    # Generate JWT token
    JWT_TOKEN=$(python3 << PYEOF
import jwt
username = "$username"
jwt_secret = "$JWT_SECRET"
token = jwt.encode({"sub": username}, jwt_secret, algorithm="HS256")
print(token)
PYEOF
)
    
    echo -e "${CYAN}Generated JWT Token:${NC}"
    echo -e "${GREEN}$JWT_TOKEN${NC}"
    echo ""
    
    # Show full details
    echo -e "${CYAN}User Details:${NC}"
    echo -e "  ${YELLOW}Username:${NC} ${GREEN}$username${NC}"
    echo -e "  ${YELLOW}API Key:${NC} ${GREEN}${api_key:0:10}...${api_key: -10}${NC}"
    echo -e "  ${YELLOW}API Secret:${NC} ${GREEN}${api_secret:0:10}...${api_secret: -10}${NC}"
    echo -e "  ${YELLOW}Created:${NC} ${GREEN}$TIMESTAMP${NC}"
    echo -e "  ${YELLOW}Domain:${NC} ${GREEN}$DOMAIN${NC}"
    echo ""
}

# Remove user
remove_user() {
    local username="$1"
    
    if [ -z "$username" ]; then
        echo -e "${RED}❌ Missing username${NC}"
        exit 1
    fi
    
    check_db
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}REMOVE USER${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if ! jq -e ".$username" "$USERS_DB" > /dev/null 2>&1; then
        echo -e "${RED}❌ User not found: $username${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}⚠ Removing user: $username${NC}"
    jq "del(.[$username])" "$USERS_DB" > "$USERS_DB.tmp" && mv "$USERS_DB.tmp" "$USERS_DB"
    
    echo -e "${GREEN}✓ User removed${NC}"
    echo ""
}

# List users
list_users() {
    check_db
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}ALL CUSTOMERS${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    COUNT=$(jq 'length' "$USERS_DB")
    echo -e "${CYAN}Total customers: ${GREEN}$COUNT${NC}"
    echo ""
    
    if [ "$COUNT" -eq 0 ]; then
        echo -e "${YELLOW}No customers found${NC}"
        return
    fi
    
    echo -e "${CYAN}Username${CYAN}                    Created${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    jq -r 'to_entries[] | "\(.key | ljust(30)) \(.value.created)"' "$USERS_DB" | while read line; do
        echo -e "${GREEN}$line${NC}"
    done
    echo ""
}

# Generate JWT token
generate_token() {
    local username="$1"
    
    if [ -z "$username" ]; then
        echo -e "${RED}❌ Missing username${NC}"
        exit 1
    fi
    
    check_db
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}GENERATE JWT TOKEN${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if ! jq -e ".$username" "$USERS_DB" > /dev/null 2>&1; then
        echo -e "${RED}❌ User not found: $username${NC}"
        exit 1
    fi
    
    JWT_TOKEN=$(python3 << PYEOF
import jwt
username = "$username"
jwt_secret = "$JWT_SECRET"
token = jwt.encode({"sub": username}, jwt_secret, algorithm="HS256")
print(token)
PYEOF
)
    
    echo -e "${CYAN}User: ${GREEN}$username${NC}"
    echo -e "${CYAN}Token:${NC}"
    echo -e "${GREEN}$JWT_TOKEN${NC}"
    echo ""
    echo -e "${CYAN}Batch file command (Windows):${NC}"
    echo -e "${GREEN}@echo off${NC}"
    echo -e "${GREEN}\"C:\\Program Files\\nodejs\\npx.cmd\" -y mcp-remote \"https://$DOMAIN/messages\" --header \"Authorization:Bearer $JWT_TOKEN\"${NC}"
    echo ""
}

# Show user info
show_info() {
    local username="$1"
    
    if [ -z "$username" ]; then
        echo -e "${RED}❌ Missing username${NC}"
        exit 1
    fi
    
    check_db
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}USER INFO${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if ! jq -e ".$username" "$USERS_DB" > /dev/null 2>&1; then
        echo -e "${RED}❌ User not found: $username${NC}"
        exit 1
    fi
    
    API_KEY=$(jq -r ".[$username].binance_api_key" "$USERS_DB")
    API_SECRET=$(jq -r ".[$username].binance_api_secret" "$USERS_DB")
    CREATED=$(jq -r ".[$username].created" "$USERS_DB")
    
    echo -e "${CYAN}Username:${NC} ${GREEN}$username${NC}"
    echo -e "${CYAN}API Key:${NC} ${GREEN}${API_KEY:0:10}...${API_KEY: -10}${NC}"
    echo -e "${CYAN}API Secret:${NC} ${GREEN}${API_SECRET:0:10}...${API_SECRET: -10}${NC}"
    echo -e "${CYAN}Created:${NC} ${GREEN}$CREATED${NC}"
    echo -e "${CYAN}Domain:${NC} ${GREEN}$DOMAIN${NC}"
    echo ""
}

# Setup complete client files
setup_client() {
    local username="$1"
    
    if [ -z "$username" ]; then
        echo -e "${RED}❌ Missing username${NC}"
        exit 1
    fi
    
    check_db
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}GENERATE CLIENT SETUP FILES${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if ! jq -e ".$username" "$USERS_DB" > /dev/null 2>&1; then
        echo -e "${RED}❌ User not found: $username${NC}"
        exit 1
    fi
    
    # Generate token
    JWT_TOKEN=$(python3 << PYEOF
import jwt
username = "$username"
jwt_secret = "$JWT_SECRET"
token = jwt.encode({"sub": username}, jwt_secret, algorithm="HS256")
print(token)
PYEOF
)
    
    # Create setup directory
    mkdir -p "$SETUP_DIR/$username"
    SETUP_PATH="$SETUP_DIR/$username"
    
    # Extract customer name (remove "customer_" prefix)
    CUSTOMER_NAME="${username#customer_}"
    
    # Create batch file
    cat > "$SETUP_PATH/$CUSTOMER_NAME-binance-mcp.bat" << BATCHEOF
@echo off
"C:\Program Files\nodejs\npx.cmd" -y mcp-remote "https://$DOMAIN/messages" --header "Authorization:Bearer $JWT_TOKEN"
BATCHEOF
    
    # Create Claude config
    cat > "$SETUP_PATH/claude_desktop_config.json" << JSONEOF
{
  "mcpServers": {
    "binance-futures": {
      "command": "C:\\\\$CUSTOMER_NAME-binance-mcp.bat",
      "args": []
    }
  }
}
JSONEOF
    
    # Create setup instructions
    cat > "$SETUP_PATH/SETUP_INSTRUCTIONS.md" << INSTREOF
# Binance Futures MCP Setup - $CUSTOMER_NAME

## Quick Start (5 minutes)

### Step 1: Copy Batch File
- Copy file: \`$CUSTOMER_NAME-binance-mcp.bat\`
- Paste to: \`C:\\$CUSTOMER_NAME-binance-mcp.bat\`

### Step 2: Update Claude Desktop Config
- Open: \`%APPDATA%\Claude\claude_desktop_config.json\`
- Copy the content from: \`claude_desktop_config.json\`
- Paste it into your Claude Desktop config

### Step 3: Restart Claude Desktop
\`\`\`
1. Close Claude Desktop completely
2. Kill any Claude processes in Task Manager
3. Reopen Claude Desktop
\`\`\`

### Step 4: Verify Connection
- Look for hammer icon next to "binance-futures"
- Should show green checkmark ✓

### Step 5: Test
Ask Claude in chat:
\`\`\`
Check my Binance account balance
\`\`\`

## Your Credentials

- **Domain**: $DOMAIN
- **Username**: $username
- **JWT Token**: \`$JWT_TOKEN\`

## Available Commands

Once connected, you can ask Claude:
- "Check my Binance account balance"
- "What's the current BTC price?"
- "Place a 0.01 BTC buy order on BTCUSDT"
- "Close my ETHUSDT position"
- "List my open orders"

## Support

If you have issues:
1. Verify batch file exists: \`C:\\$CUSTOMER_NAME-binance-mcp.bat\`
2. Check Node.js installed: \`node --version\`
3. Verify config is valid JSON
4. Restart Claude completely
5. Check if hammer icon shows ✓

---
Setup generated: $TIMESTAMP
INSTREOF
    
    # Show results
    echo -e "${GREEN}✓ Setup files created${NC}"
    echo ""
    echo -e "${CYAN}Location: ${GREEN}$SETUP_PATH${NC}"
    echo ""
    echo -e "${CYAN}Files:${NC}"
    ls -lh "$SETUP_PATH/" | tail -n +2 | awk '{print "  " $9 " (" $5 ")"}'
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "  ${GREEN}1. Send all files in $SETUP_PATH to the client${NC}"
    echo -e "  ${GREEN}2. They follow SETUP_INSTRUCTIONS.md${NC}"
    echo ""
}

# Main
show_banner

if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

COMMAND="$1"

case "$COMMAND" in
    add)
        check_root
        add_user "$2" "$3" "$4"
        ;;
    remove)
        check_root
        remove_user "$2"
        ;;
    list)
        list_users
        ;;
    token)
        generate_token "$2"
        ;;
    info)
        show_info "$2"
        ;;
    setup)
        check_root
        setup_client "$2"
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
