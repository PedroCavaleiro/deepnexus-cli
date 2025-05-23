#!/bin/bash

REPO_URL="https://github.com/PedroCavaleiro/deepnexus-cli"
INSTALL_DIR="$HOME/.local/share/deepnexus-cli"
BIN_LINK="$HOME/.local/bin/deepnexus-cli"

echo "Installing deepnexus-cli..."

# Step 1: Install required Python packages
echo "Installing required Python packages..."
pip3 install --user tabulate pyfiglet

# Step 2: Create install directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$(dirname "$BIN_LINK")"

# Step 3: Download and extract latest repo version
TMP_DIR=$(mktemp -d)
echo "Downloading latest release from $REPO_URL..."
curl -fsSL "$REPO_URL/archive/refs/heads/main.zip" -o "$TMP_DIR/repo.zip"
unzip -q "$TMP_DIR/repo.zip" -d "$TMP_DIR"
cp -r "$TMP_DIR/deepnexus-cli-main/"* "$INSTALL_DIR"

# Step 4: Create symlink or launcher script
echo "Setting up CLI launcher..."
echo -e "#!/bin/bash\npython3 \"$INSTALL_DIR/deepnexus-cli.py\" \"\$@\"" > "$BIN_LINK"
chmod +x "$BIN_LINK"

# Step 5: Add ~/.local/bin to PATH if needed
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "Adding ~/.local/bin to PATH in ~/.bashrc..."
    echo 'export PATH="$PATH:$HOME/.local/bin"' >> "$HOME/.bashrc"
    export PATH="$PATH:$HOME/.local/bin"
fi

# Step 6: Ask to auto-run on login
read -p "Do you want to run deepnexus-cli at shell login? (y/n): " run_login
if [[ "$run_login" =~ ^[Yy]$ ]]; then
    echo "$BIN_LINK" >> "$HOME/.bash_profile"
fi

echo "✅ Installation complete. Run 'deepnexus-cli' to start the tool."
