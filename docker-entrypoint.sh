#!/bin/bash
set -e

# Initialize vaults.json if it doesn't exist
# This handles the case where the config volume is mounted but empty
CONFIG_FILE="/app/config/vaults.json"
DEFAULT_CONFIG="/app/defaults/vaults.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "No vaults.json found, creating default configuration..."
    
    # Ensure config directory exists and is writable
    mkdir -p /app/config
    
    # Copy default config
    if [ -f "$DEFAULT_CONFIG" ]; then
        cp "$DEFAULT_CONFIG" "$CONFIG_FILE"
        echo "Created default vaults.json from template"
    else
        # Create minimal empty config
        echo '{"vaults": {}, "default_vault": null}' > "$CONFIG_FILE"
        echo "Created empty vaults.json"
    fi
fi

# Execute the main command
exec "$@"

