#!/bin/bash

REPO_URL="https://github.com/PedroCavaleiro/deepnexus-cli"
REPO_BRANCH="main"
INSTALL_DIR="$HOME/.local/share/deepnexus-cli"
BIN_LINK="$HOME/.local/bin/deepnexus-cli"
TMP_DIR=$(mktemp -d)

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

add_to_shell_login() {
    SHELL_NAME=$(basename "$SHELL")
    STARTUP_CMD="$BIN_LINK"

    case "$SHELL_NAME" in
        bash)
            echo "$STARTUP_CMD" >> "$HOME/.bashrc"
            ;;
        zsh)
            echo "$STARTUP_CMD" >> "$HOME/.zshrc"
            ;;
        fish)
            mkdir -p "$HOME/.config/fish"
            echo "$STARTUP_CMD" >> "$HOME/.config/fish/config.fish"
            ;;
        *)
            echo "Shell not recognized for auto-start. Add '$STARTUP_CMD' manually to your login script."
            ;;
    esac
}

create_launcher() {
    echo -e "#!/bin/bash\npython3 \"$INSTALL_DIR/deepnexus-cli.py\" \"\$@\"" > "$BIN_LINK"
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

    # Step 4: Create CLI launcher
    create_launcher

    # Step 5: Ensure local bin is in PATH
    ensure_local_bin_in_path

    # Step 6: Ask for login startup
    read -p "Do you want to auto-run deepnexus-cli at shell login? (y/n): " run_login
    if [[ "$run_login" =~ ^[Yy]$ ]]; then
        add_to_shell_login
    fi

    echo "✅ Installation complete. Run 'deepnexus-cli' to start the tool."
}

update_tool() {
    echo "Updating deepnexus-cli..."
    rm -rf "$INSTALL_DIR"
    install_tool
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
