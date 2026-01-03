#!/bin/bash
set -e

# Entrypoint script for Obsidian Web Reader
# Fixes permissions on mounted volumes, then runs the app as appuser

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[entrypoint]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[entrypoint]${NC} $1"
}

log_error() {
    echo -e "${RED}[entrypoint]${NC} $1"
}

# Get appuser UID/GID
APPUSER_UID=$(id -u appuser 2>/dev/null || echo "1000")
APPUSER_GID=$(id -g appuser 2>/dev/null || echo "1000")

# Fix permissions on config directory
if [ -d "/app/config" ]; then
    log_info "Fixing permissions on /app/config..."
    chown -R appuser:appuser /app/config 2>/dev/null || log_warn "Could not change ownership of /app/config (may be read-only mount)"
    chmod -R u+rw /app/config 2>/dev/null || log_warn "Could not change permissions of /app/config"
fi

# Create vaults.json if it doesn't exist
if [ ! -f "/app/config/vaults.json" ]; then
    log_info "Creating default vaults.json..."
    echo '{"vaults": {}, "default_vault": null}' > /app/config/vaults.json 2>/dev/null || log_warn "Could not create vaults.json"
    chown appuser:appuser /app/config/vaults.json 2>/dev/null || true
fi

# Handle case where vaults.json is a directory (Docker mount issue)
if [ -d "/app/config/vaults.json" ]; then
    log_warn "/app/config/vaults.json is a directory (Docker mount target didn't exist on host)"
    log_info "Removing directory and creating file..."
    rmdir /app/config/vaults.json 2>/dev/null || rm -rf /app/config/vaults.json
    echo '{"vaults": {}, "default_vault": null}' > /app/config/vaults.json
    chown appuser:appuser /app/config/vaults.json 2>/dev/null || true
fi

# Fix permissions on data directory
if [ -d "/app/data" ]; then
    log_info "Fixing permissions on /app/data..."
    chown -R appuser:appuser /app/data 2>/dev/null || log_warn "Could not change ownership of /app/data"
fi

# Fix permissions on vaults directory (for cloned repos)
if [ -d "/data/vaults" ]; then
    # Only fix if it's writable (not read-only mount)
    if touch /data/vaults/.write_test 2>/dev/null; then
        rm /data/vaults/.write_test
        log_info "Fixing permissions on /data/vaults..."
        chown -R appuser:appuser /data/vaults 2>/dev/null || true
    fi
fi

# Create vaults directory if it doesn't exist (for dynamically added vaults)
VAULTS_DIR="${VAULTS_DIR:-/app/vaults}"
if [ ! -d "$VAULTS_DIR" ]; then
    log_info "Creating vaults directory at $VAULTS_DIR..."
    mkdir -p "$VAULTS_DIR"
    chown appuser:appuser "$VAULTS_DIR"
fi

log_info "Starting application as appuser..."

# Execute the main command as appuser
exec gosu appuser "$@"

