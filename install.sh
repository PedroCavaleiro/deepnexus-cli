#!/bin/bash

REPO_URL="https://github.com/PedroCavaleiro/deepnexus-cli"
REPO_BRANCH="main"
INSTALL_DIR="$HOME/.local/share/deepnexus-cli"
BIN_LINK="$HOME/.local/bin/deepnexus-cli"
TMP_DIR=$(mktemp -d)
SHELL_NAME=$(basename "$SHELL")
STARTUP_CMD="$BIN_LINK"

install_package() {
    PACKAGE_NAME=$1
    APT_NAME=${2:-}

    if ! python3 -c "import $PACKAGE_NAME" &>/dev/null; then
        if [ -n "$APT_NAME" ]; then
            echo "Trying to install $PACKAGE_NAME via apt..."
            if ! sudo apt-get install -y "$APT_NAME"; then
                echo "Falling back to pip for $PACKAGE_NAME"
                pip3 install --user "$PACKAGE_NAME"
            fi
        else
            echo "Installing $PACKAGE_NAME via pip..."
            pip3 install --user "$PACKAGE_NAME"
        fi
    else
        echo "$PACKAGE_NAME already installed."
    fi
}

set_startup() {
    case "$SHELL_NAME" in
        bash)
            SHELL_FILE="$HOME/.bashrc"
            ;;
        zsh)
            SHELL_FILE="$HOME/.zshrc"
            ;;
        fish)
            SHELL_FILE="$HOME/.config/fish/config.fish"
            ;;
        *)
            echo "Shell not recognized for auto-start."
            return
            ;;
    esac

    if [[ "$run_login" =~ ^[Yy]$ ]]; then
        if ! grep -Fxq "$STARTUP_CMD" "$SHELL_FILE"; then
            echo "$STARTUP_CMD" >> "$SHELL_FILE"
            echo "✔ Added deepnexus-cli to $SHELL_NAME startup."
        else
            echo "ℹ deepnexus-cli already set to auto-run in $SHELL_FILE"
        fi
    else
        if grep -Fxq "$STARTUP_CMD" "$SHELL_FILE"; then
            sed -i "\|$STARTUP_CMD|d" "$SHELL_FILE"
            echo "✘ Removed deepnexus-cli from $SHELL_NAME startup."
        else
            echo "ℹ deepnexus-cli was not set to auto-run in $SHELL_FILE"
        fi
    fi
}

create_launcher() {
    cat > "$BIN_LINK" <<EOF
#!/bin/bash

INSTALLER="\$HOME/.local/share/deepnexus-cli/install.sh"
CLI_MAIN="\$HOME/.local/share/deepnexus-cli/deepnexus-cli.py"

if [[ "\$DEEPNEXUS_INTERNAL_CALL" == "1" ]]; then
    exit 0
fi

if [[ "\$1" == "update" || "\$1" == "uninstall" ]]; then
    bash "\$INSTALLER" "\$1"
else
    python3 "\$CLI_MAIN" "\$@"
fi
EOF
    chmod +x "$BIN_LINK"
}

ensure_local_bin_in_path() {
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo "Adding ~/.local/bin to PATH in ~/.bashrc..."
        echo 'export PATH="$PATH:$HOME/.local/bin"' >> "$HOME/.bashrc"
        export PATH="$PATH:$HOME/.local/bin"
    fi
}

install_tool() {
    echo "Installing deepnexus-cli..."

    # Step 1: Install Python dependencies
    install_package tabulate python3-tabulate
    install_package pyfiglet

    # Step 2: Prepare install directories
    mkdir -p "$INSTALL_DIR" "$(dirname "$BIN_LINK")"

    # Step 3: Download latest version
    echo "Downloading latest release from $REPO_URL..."
    curl -fsSL "$REPO_URL/archive/refs/heads/$REPO_BRANCH.zip" -o "$TMP_DIR/repo.zip"
    unzip -q "$TMP_DIR/repo.zip" -d "$TMP_DIR"
    cp -r "$TMP_DIR/deepnexus-cli-$REPO_BRANCH/"* "$INSTALL_DIR"
    rm -rf "$TMP_DIR"

    create_launcher

    ensure_local_bin_in_path

    read -p "Do you want to auto-run deepnexus-cli at shell login? (y/n): " run_login
    set_startup

    echo "✅ Installation complete. Run 'deepnexus-cli' to start the tool."
}

update_tool() {
    echo "Updating deepnexus-cli..."

    # Optional: backup existing configs
    if [ -d "$INSTALL_DIR/configs" ]; then
        CONFIG_BACKUP="$INSTALL_DIR/configs_backup_$(date +%s)"
        cp -r "$INSTALL_DIR/configs" "$CONFIG_BACKUP"
        echo "📦 Backup of configs saved to $CONFIG_BACKUP"
    fi

    # Download latest version
    echo "Downloading latest release from $REPO_URL..."
    mkdir -p "$TMP_DIR"
    curl -fsSL "$REPO_URL/archive/refs/heads/$REPO_BRANCH.zip" -o "$TMP_DIR/repo.zip"
    unzip -q "$TMP_DIR/repo.zip" -d "$TMP_DIR"

    # Copy all files except the configs folder
    rsync -a --exclude 'configs/' "$TMP_DIR/deepnexus-cli-$REPO_BRANCH/" "$INSTALL_DIR/"

    rm -rf "$TMP_DIR"

    create_launcher
    ensure_local_bin_in_path

    echo "✅ Update complete."
}

uninstall_tool() {
    echo "Uninstalling deepnexus-cli..."
    rm -rf "$INSTALL_DIR"
    rm -f "$BIN_LINK"

    sed -i '/deepnexus-cli/d' "$HOME/.bashrc" 2>/dev/null
    sed -i '/deepnexus-cli/d' "$HOME/.zshrc" 2>/dev/null
    sed -i '/deepnexus-cli/d' "$HOME/.config/fish/config.fish" 2>/dev/null

    echo "✅ Uninstallation complete."
}

# --- Entry Point ---
case "$1" in
    uninstall)
        uninstall_tool
        ;;
    update)
        update_tool
        ;;
    *)
        install_tool
        ;;
esac
