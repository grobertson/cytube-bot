#!/bin/bash
# Deployment script for Rosey Bot
# Usage: ./scripts/deploy.sh <environment>

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/backups"
LOG_FILE="$PROJECT_ROOT/logs/deploy.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Print colored message
print_msg() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Usage information
usage() {
    cat << EOF
Usage: $0 <environment>

Arguments:
    environment     Environment to deploy (test or prod)

Environment variables:
    CYTUBEBOT_TEST_PASSWORD    Password for test bot
    CYTUBEBOT_PROD_PASSWORD    Password for production bot

Examples:
    $0 test     # Deploy to test channel
    $0 prod     # Deploy to production

EOF
    exit 1
}

# Validate environment
ENVIRONMENT=$1

if [[ -z "$ENVIRONMENT" ]]; then
    echo "Error: Environment required"
    usage
fi

if [[ "$ENVIRONMENT" != "test" && "$ENVIRONMENT" != "prod" ]]; then
    echo "Error: Environment must be 'test' or 'prod'"
    usage
fi

print_msg "$BLUE" "═══════════════════════════════════════════"
print_msg "$BLUE" "  Deploying to ${ENVIRONMENT^^}"
print_msg "$BLUE" "═══════════════════════════════════════════"
echo ""

log "INFO" "Deployment started for $ENVIRONMENT"

# Step 1: Create backup
print_msg "$BLUE" "▸ Creating backup..."

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ENV_BACKUP_DIR="$BACKUP_DIR/$ENVIRONMENT"
BACKUP_PATH="$ENV_BACKUP_DIR/backup_$TIMESTAMP"

mkdir -p "$ENV_BACKUP_DIR"

# Copy current deployment if it exists
if [[ -L "$PROJECT_ROOT/current" ]] && [[ -e "$PROJECT_ROOT/current" ]]; then
    CURRENT_PATH=$(readlink -f "$PROJECT_ROOT/current")
    cp -r "$CURRENT_PATH" "$BACKUP_PATH"
    print_msg "$GREEN" "✓ Backup created: $BACKUP_PATH"
    log "INFO" "Backup created at $BACKUP_PATH"
else
    # First deployment, create empty backup
    mkdir -p "$BACKUP_PATH"
    print_msg "$YELLOW" "⚠ No previous deployment to backup"
    log "WARN" "No previous deployment found"
fi

# Step 2: Create new deployment directory
print_msg "$BLUE" "▸ Creating new deployment..."

NEW_DEPLOYMENT="$PROJECT_ROOT/deployments/deploy_$TIMESTAMP"
mkdir -p "$NEW_DEPLOYMENT"

# Copy project files
cp -r "$PROJECT_ROOT/lib" "$NEW_DEPLOYMENT/"
cp -r "$PROJECT_ROOT/common" "$NEW_DEPLOYMENT/"
cp -r "$PROJECT_ROOT/bots" "$NEW_DEPLOYMENT/"
cp -r "$PROJECT_ROOT/web" "$NEW_DEPLOYMENT/"
cp "$PROJECT_ROOT/requirements.txt" "$NEW_DEPLOYMENT/"

# Copy VERSION file if it exists
if [[ -f "$PROJECT_ROOT/VERSION" ]]; then
    cp "$PROJECT_ROOT/VERSION" "$NEW_DEPLOYMENT/"
fi

print_msg "$GREEN" "✓ Deployment prepared: $NEW_DEPLOYMENT"
log "INFO" "New deployment created at $NEW_DEPLOYMENT"

# Step 3: Create config symlink
print_msg "$BLUE" "▸ Configuring environment..."

CONFIG_FILE="config-${ENVIRONMENT}.json"

if [[ ! -f "$PROJECT_ROOT/$CONFIG_FILE" ]]; then
    print_msg "$RED" "✗ Config file not found: $CONFIG_FILE"
    log "ERROR" "Config file missing: $CONFIG_FILE"
    exit 1
fi

ln -sf "$PROJECT_ROOT/$CONFIG_FILE" "$NEW_DEPLOYMENT/config.json"
print_msg "$GREEN" "✓ Configuration linked"
log "INFO" "Config linked: $CONFIG_FILE"

# Step 4: Install dependencies
print_msg "$BLUE" "▸ Installing dependencies..."

cd "$NEW_DEPLOYMENT"

if command -v python3 &> /dev/null; then
    python3 -m pip install -q -r requirements.txt
    print_msg "$GREEN" "✓ Dependencies installed"
    log "INFO" "Dependencies installed"
else
    print_msg "$RED" "✗ Python 3 not found"
    log "ERROR" "Python 3 not found"
    exit 1
fi

cd "$PROJECT_ROOT"

# Step 5: Stop current bot
print_msg "$BLUE" "▸ Stopping current bot..."

if systemctl is-active --quiet cytube-bot; then
    systemctl stop cytube-bot
    sleep 2
    print_msg "$GREEN" "✓ Bot stopped"
    log "INFO" "Bot stopped"
else
    print_msg "$YELLOW" "⚠ Bot was not running"
    log "WARN" "Bot was not running"
fi

# Step 6: Update current symlink
print_msg "$BLUE" "▸ Switching to new deployment..."

rm -f "$PROJECT_ROOT/current"
ln -s "$NEW_DEPLOYMENT" "$PROJECT_ROOT/current"

print_msg "$GREEN" "✓ Deployment activated"
log "INFO" "Symlink updated to $NEW_DEPLOYMENT"

# Step 7: Start bot
print_msg "$BLUE" "▸ Starting bot..."

systemctl start cytube-bot
sleep 3

if systemctl is-active --quiet cytube-bot; then
    print_msg "$GREEN" "✓ Bot started"
    log "INFO" "Bot started successfully"
else
    print_msg "$RED" "✗ Bot failed to start"
    log "ERROR" "Bot failed to start"
    
    # Automatic rollback
    print_msg "$YELLOW" "⚠ Rolling back to previous version..."
    if [[ -d "$BACKUP_PATH" ]]; then
        rm -f "$PROJECT_ROOT/current"
        ln -s "$BACKUP_PATH" "$PROJECT_ROOT/current"
        systemctl start cytube-bot
        print_msg "$YELLOW" "⚠ Rolled back to backup"
        log "WARN" "Automatic rollback performed"
    fi
    exit 1
fi

# Step 8: Wait for startup
STARTUP_DELAY=10
if [[ "$ENVIRONMENT" == "prod" ]]; then
    STARTUP_DELAY=30
fi

print_msg "$BLUE" "▸ Waiting ${STARTUP_DELAY}s for startup..."
sleep "$STARTUP_DELAY"

# Success
print_msg "$BLUE" "═══════════════════════════════════════════"
print_msg "$GREEN" "✓ Deployment completed successfully"
print_msg "$BLUE" "═══════════════════════════════════════════"
echo ""

log "INFO" "Deployment completed successfully"

# Print deployment info
print_msg "$BLUE" "Deployment Details:"
print_msg "$NC" "  Environment: $ENVIRONMENT"
print_msg "$NC" "  Path: $NEW_DEPLOYMENT"
print_msg "$NC" "  Backup: $BACKUP_PATH"
print_msg "$NC" "  Time: $(date)"
echo ""

exit 0
