#!/bin/bash
#
# Enhanced rollback script for Rosey Bot
#
# Provides multiple rollback modes:
#   1. Auto-rollback (triggered by failed deployment)
#   2. Manual rollback to previous version
#   3. Rollback to specific version
#   4. List available rollback points
#
# Usage:
#   ./scripts/rollback.sh <env> [mode] [version]
#
# Examples:
#   ./scripts/rollback.sh prod auto
#   ./scripts/rollback.sh prod manual
#   ./scripts/rollback.sh prod specific 2025-01-15_14-30-00
#   ./scripts/rollback.sh prod list

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
BACKUP_DIR="$PROJECT_ROOT/backups"
DEPLOY_DIR="$PROJECT_ROOT/deployments"
ROLLBACK_LOG="$LOG_DIR/rollback.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Logging function
log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" >> "$ROLLBACK_LOG"
}

# Print colored message
print_msg() {
    local color=$1
    local msg=$2
    echo -e "${color}${msg}${NC}"
    log "$msg"
}

# Usage information
usage() {
    cat << EOF
Usage: $0 <env> [mode] [version]

Arguments:
  env       Environment (test|prod)
  mode      Rollback mode (auto|manual|specific|list) [default: manual]
  version   Specific version timestamp (required for 'specific' mode)

Modes:
  auto      Automatic rollback to last backup (used by deploy.sh)
  manual    Interactive rollback to previous deployment
  specific  Rollback to a specific backup version
  list      List available rollback points

Examples:
  $0 prod list
  $0 prod manual
  $0 prod specific 2025-01-15_14-30-00
  $0 test auto

EOF
    exit 1
}

# List available backups
list_backups() {
    local env=$1
    local backup_path="$BACKUP_DIR/$env"
    
    print_msg "$BLUE" "Available rollback points for $env:"
    echo ""
    
    if [ ! -d "$backup_path" ]; then
        print_msg "$YELLOW" "No backups found for $env"
        return
    fi
    
    local count=0
    for backup in $(ls -t "$backup_path"); do
        if [ -d "$backup_path/$backup" ]; then
            count=$((count + 1))
            local timestamp=$(echo "$backup" | sed 's/backup_//')
            local size=$(du -sh "$backup_path/$backup" | cut -f1)
            
            # Try to read VERSION file from backup
            local version="unknown"
            if [ -f "$backup_path/$backup/VERSION" ]; then
                version=$(cat "$backup_path/$backup/VERSION")
            fi
            
            printf "  %2d. %s  (version: %s, size: %s)\n" "$count" "$timestamp" "$version" "$size"
        fi
    done
    
    if [ $count -eq 0 ]; then
        print_msg "$YELLOW" "No backups found"
    else
        echo ""
        print_msg "$GREEN" "Found $count backup(s)"
    fi
}

# Get the most recent backup
get_latest_backup() {
    local env=$1
    local backup_path="$BACKUP_DIR/$env"
    
    if [ ! -d "$backup_path" ]; then
        echo ""
        return
    fi
    
    # Get most recent backup directory
    local latest=$(ls -t "$backup_path" | head -n 1)
    if [ -n "$latest" ]; then
        echo "$backup_path/$latest"
    else
        echo ""
    fi
}

# Perform rollback
perform_rollback() {
    local env=$1
    local backup_source=$2
    
    if [ ! -d "$backup_source" ]; then
        print_msg "$RED" "✗ Backup source not found: $backup_source"
        return 1
    fi
    
    print_msg "$YELLOW" "═══════════════════════════════════════"
    print_msg "$YELLOW" "  ROLLING BACK - $env"
    print_msg "$YELLOW" "═══════════════════════════════════════"
    echo ""
    
    # Get version from backup
    local backup_version="unknown"
    if [ -f "$backup_source/VERSION" ]; then
        backup_version=$(cat "$backup_source/VERSION")
    fi
    
    print_msg "$BLUE" "→ Rolling back to version: $backup_version"
    print_msg "$BLUE" "→ Backup source: $backup_source"
    
    # Stop the bot
    print_msg "$BLUE" "→ Stopping bot service..."
    if systemctl stop cytube-bot-$env 2>&1 | tee -a "$ROLLBACK_LOG"; then
        print_msg "$GREEN" "✓ Bot stopped"
    else
        print_msg "$YELLOW" "⚠ Failed to stop bot (may not be running)"
    fi
    
    # Create rollback deployment directory
    local rollback_timestamp=$(date '+%Y%m%d_%H%M%S')
    local rollback_dir="$DEPLOY_DIR/rollback_${rollback_timestamp}"
    
    print_msg "$BLUE" "→ Creating rollback deployment..."
    mkdir -p "$rollback_dir"
    
    # Copy backup to rollback deployment
    cp -r "$backup_source"/* "$rollback_dir/"
    print_msg "$GREEN" "✓ Rollback deployment created"
    
    # Link config
    print_msg "$BLUE" "→ Linking configuration..."
    ln -sf "$PROJECT_ROOT/config-$env.json" "$rollback_dir/config.json"
    print_msg "$GREEN" "✓ Configuration linked"
    
    # Update current symlink
    print_msg "$BLUE" "→ Updating current deployment symlink..."
    rm -f "$DEPLOY_DIR/current"
    ln -sf "$rollback_dir" "$DEPLOY_DIR/current"
    print_msg "$GREEN" "✓ Symlink updated"
    
    # Start the bot
    print_msg "$BLUE" "→ Starting bot service..."
    if systemctl start cytube-bot-$env 2>&1 | tee -a "$ROLLBACK_LOG"; then
        print_msg "$GREEN" "✓ Bot started"
    else
        print_msg "$RED" "✗ Failed to start bot"
        return 1
    fi
    
    # Wait for startup
    local startup_delay=30
    if [ "$env" = "test" ]; then
        startup_delay=10
    fi
    
    print_msg "$BLUE" "→ Waiting ${startup_delay}s for bot startup..."
    sleep $startup_delay
    
    # Verify bot is running
    if systemctl is-active --quiet cytube-bot-$env; then
        print_msg "$GREEN" "✓ Bot is running"
        echo ""
        print_msg "$GREEN" "════════════════════════════════════════"
        print_msg "$GREEN" "  ROLLBACK SUCCESSFUL"
        print_msg "$GREEN" "════════════════════════════════════════"
        echo ""
        print_msg "$GREEN" "Rolled back to version: $backup_version"
        return 0
    else
        print_msg "$RED" "✗ Bot failed to start after rollback"
        return 1
    fi
}

# Main script
main() {
    # Parse arguments
    if [ $# -lt 1 ]; then
        usage
    fi
    
    ENV=$1
    MODE=${2:-manual}
    VERSION=$3
    
    # Validate environment
    if [ "$ENV" != "test" ] && [ "$ENV" != "prod" ]; then
        print_msg "$RED" "Error: Invalid environment '$ENV'. Must be 'test' or 'prod'"
        usage
    fi
    
    # Handle list mode
    if [ "$MODE" = "list" ]; then
        list_backups "$ENV"
        exit 0
    fi
    
    # Handle rollback modes
    case "$MODE" in
        auto)
            # Auto rollback to latest backup (used by deploy.sh)
            print_msg "$YELLOW" "Starting automatic rollback..."
            LATEST_BACKUP=$(get_latest_backup "$ENV")
            
            if [ -z "$LATEST_BACKUP" ]; then
                print_msg "$RED" "✗ No backups available for rollback"
                exit 1
            fi
            
            perform_rollback "$ENV" "$LATEST_BACKUP"
            exit $?
            ;;
        
        manual)
            # Interactive rollback to previous deployment
            print_msg "$YELLOW" "Starting manual rollback..."
            list_backups "$ENV"
            echo ""
            
            LATEST_BACKUP=$(get_latest_backup "$ENV")
            if [ -z "$LATEST_BACKUP" ]; then
                print_msg "$RED" "✗ No backups available for rollback"
                exit 1
            fi
            
            read -p "Rollback to most recent backup? [y/N] " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_msg "$YELLOW" "Rollback cancelled"
                exit 0
            fi
            
            perform_rollback "$ENV" "$LATEST_BACKUP"
            exit $?
            ;;
        
        specific)
            # Rollback to specific version
            if [ -z "$VERSION" ]; then
                print_msg "$RED" "Error: Version timestamp required for 'specific' mode"
                echo ""
                list_backups "$ENV"
                exit 1
            fi
            
            BACKUP_PATH="$BACKUP_DIR/$ENV/backup_$VERSION"
            
            if [ ! -d "$BACKUP_PATH" ]; then
                print_msg "$RED" "✗ Backup not found: $VERSION"
                echo ""
                list_backups "$ENV"
                exit 1
            fi
            
            print_msg "$YELLOW" "Rolling back to specific version: $VERSION"
            perform_rollback "$ENV" "$BACKUP_PATH"
            exit $?
            ;;
        
        *)
            print_msg "$RED" "Error: Invalid mode '$MODE'"
            usage
            ;;
    esac
}

main "$@"
