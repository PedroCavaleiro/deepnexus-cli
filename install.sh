#!/bin/bash

REPO_URL="https://github.com/PedroCavaleiro/deepnexus-cli"
INSTALL_DIR="$HOME/.local/share/deepnexus-cli"
BIN_LINK="$HOME/.local/bin/deepnexus-cli"

install_package() {
    PACKAGE_NAME=$1
    APT_NAME=${2:-}

    if ! python3 -c "import $PACKAGE_NAME" 2>/dev/null; then
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

echo "Installing deepnexus-cli..."

# Step 1: Install required Python packages
install_package tabulate python3-tabulate
install_package pyfiglet  # skip apt, it's usually not available

# Step 2: Create install directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$(dirname "$BIN_LINK")"

# Step 3: Download and extract latest repo version
TMP_DIR=$(mktemp -d)
echo "Downloading latest release from $REPO_URL..."
curl -fsSL "$REPO_URL/archive/refs/heads/main.zip" -o "$TMP_DIR/repo.zip"
unzip -q "$TMP_DIR/repo.zip" -d "$TMP_DIR"
cp -r "$TMP_DIR/deepnexus-cli-main/"* "$INSTALL_DIR"
rm -rf "$TMP_DIR"

# Step 4: Create CLI launcher
echo "Creating launcher at $BIN_LINK..."
echo -e "#!/bin/bash\npython3 \"$INSTALL_DIR/deepnexus-cli.py\" \"\$@\"" > "$BIN_LINK"
chmod +x "$BIN_LINK"

# Step 5: Ensure ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "Adding ~/.local/bin to PATH in ~/.bashrc..."
    echo 'export PATH="$PATH:$HOME/.local/bin"' >> "$HOME/.bashrc"
    export PATH="$PATH:$HOME/.local/bin"
fi

# Step 6: Ask user if they want to run it at shell login
read -p "Do you want to run deepnexus-cli at shell login? (y/n): " run_login
if [[ "$run_login" =~ ^[Yy]$ ]]; then
    LOGIN_FILE="$HOME/.bash_profile"
    [[ -f "$HOME/.bashrc" ]] && LOGIN_FILE="$HOME/.bashrc"
    echo "$BIN_LINK" >> "$LOGIN_FILE"
fi

echo "✅ Installation complete. Run 'deepnexus-cli' to start the tool."
