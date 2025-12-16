#!/bin/bash
#
# OCI CLI Installation Helper
# Installs and configures Oracle Cloud Infrastructure CLI
#

set -e

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║              OCI CLI Installation & Configuration                 ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if [ -f /etc/debian_version ]; then
            DISTRO="debian"
        elif [ -f /etc/redhat-release ]; then
            DISTRO="redhat"
        else
            DISTRO="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi

    echo "Detected OS: $OS"
    if [ "$OS" == "linux" ]; then
        echo "Distribution: $DISTRO"
    fi
    echo ""
}

# Check if OCI CLI is already installed
check_existing() {
    if command -v oci &> /dev/null; then
        VERSION=$(oci --version 2>&1 | cut -d' ' -f2)
        echo -e "${GREEN}✅ OCI CLI already installed: version $VERSION${NC}"
        echo ""
        read -p "Reinstall/update? (yes/no): " REINSTALL
        if [ "$REINSTALL" != "yes" ]; then
            echo "Keeping existing installation"
            configure_oci
            exit 0
        fi
    fi
}

# Install using pip (universal method)
install_with_pip() {
    echo "Installing OCI CLI using pip..."
    echo ""

    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        PIP_CMD="pip"
    else
        echo -e "${RED}❌ Python not found. Please install Python 3.6+${NC}"
        exit 1
    fi

    # Check pip
    if ! command -v $PIP_CMD &> /dev/null; then
        echo "Installing pip..."
        $PYTHON_CMD -m ensurepip --default-pip 2>/dev/null || {
            echo "Installing pip using get-pip.py..."
            curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
            $PYTHON_CMD get-pip.py --user
            rm get-pip.py
        }
    fi

    # Install OCI CLI
    echo "Installing oci-cli package..."
    $PIP_CMD install --user oci-cli

    # Add to PATH if needed
    USER_BASE=$($PYTHON_CMD -m site --user-base)
    USER_BIN="$USER_BASE/bin"

    if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
        echo ""
        echo "Adding $USER_BIN to PATH..."

        # Detect shell
        if [ -n "$ZSH_VERSION" ]; then
            SHELL_RC="$HOME/.zshrc"
        elif [ -n "$BASH_VERSION" ]; then
            SHELL_RC="$HOME/.bashrc"
        else
            SHELL_RC="$HOME/.profile"
        fi

        echo "export PATH=\"$USER_BIN:\$PATH\"" >> "$SHELL_RC"
        export PATH="$USER_BIN:$PATH"

        echo -e "${YELLOW}⚠️  Added OCI CLI to PATH. Restart your terminal or run:${NC}"
        echo "   source $SHELL_RC"
    fi

    echo -e "${GREEN}✅ OCI CLI installed successfully${NC}"
}

# Install using official installer (alternative)
install_official() {
    echo "Installing OCI CLI using official installer..."
    echo ""

    # Download and run installer
    bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
}

# Configure OCI CLI
configure_oci() {
    echo ""
    echo "=== OCI CLI Configuration ==="
    echo ""

    if [ -f "$HOME/.oci/config" ]; then
        echo -e "${GREEN}✅ OCI config already exists${NC}"
        echo "Location: $HOME/.oci/config"
        echo ""
        read -p "Reconfigure? (yes/no): " RECONFIG
        if [ "$RECONFIG" != "yes" ]; then
            return
        fi
    fi

    # Load values from .env if available
    ENV_FILE="$(dirname $(dirname $(dirname $0)))/.env"
    if [ -f "$ENV_FILE" ]; then
        echo "Loading values from .env file..."
        source <(grep -E '^ORACLE_' "$ENV_FILE" | sed 's/^/export /')
        echo ""
    fi

    echo "You'll need the following information:"
    echo "  • User OCID (from Oracle Cloud Console)"
    echo "  • Tenancy OCID (from Oracle Cloud Console)"
    echo "  • Region (e.g., us-chicago-1)"
    echo "  • API key location ($HOME/.oci/oci_api_key.pem)"
    echo "  • Fingerprint (after uploading public key to Oracle Cloud)"
    echo ""

    # Check if we have the values
    if [ -n "$ORACLE_USER_OCID" ] && [ -n "$ORACLE_TENANCY_OCID" ]; then
        echo "Found configuration in .env:"
        echo "  User OCID: $ORACLE_USER_OCID"
        echo "  Tenancy OCID: $ORACLE_TENANCY_OCID"
        echo "  Region: ${ORACLE_REGION:-us-chicago-1}"
        echo ""
        read -p "Use these values? (yes/no): " USE_ENV

        if [ "$USE_ENV" == "yes" ]; then
            # Create config directly
            mkdir -p "$HOME/.oci"

            cat > "$HOME/.oci/config" << EOF
[DEFAULT]
user=${ORACLE_USER_OCID}
fingerprint=${ORACLE_FINGERPRINT:-YOUR_FINGERPRINT_HERE}
key_file=${ORACLE_PRIVATE_KEY_PATH:-$HOME/.oci/oci_api_key.pem}
tenancy=${ORACLE_TENANCY_OCID}
region=${ORACLE_REGION:-us-chicago-1}
EOF

            chmod 600 "$HOME/.oci/config"
            echo -e "${GREEN}✅ OCI config created${NC}"

            if [ -z "$ORACLE_FINGERPRINT" ] || [ "$ORACLE_FINGERPRINT" == "" ]; then
                echo ""
                echo -e "${YELLOW}⚠️  Don't forget to add your fingerprint to:${NC}"
                echo "   1. $HOME/.oci/config"
                echo "   2. .env file (ORACLE_FINGERPRINT=...)"
            fi

            return
        fi
    fi

    # Run interactive setup
    echo "Running interactive configuration..."
    oci setup config
}

# Test OCI CLI connection
test_connection() {
    echo ""
    echo "=== Testing OCI Connection ==="
    echo ""

    if ! command -v oci &> /dev/null; then
        echo -e "${RED}❌ OCI CLI not found in PATH${NC}"
        return 1
    fi

    echo "Testing API connection..."
    if oci iam region list &> /dev/null; then
        echo -e "${GREEN}✅ Successfully connected to Oracle Cloud${NC}"
        echo ""
        echo "Available regions:"
        oci iam region list --output table 2>/dev/null || oci iam region list
    else
        echo -e "${YELLOW}⚠️  Could not connect to Oracle Cloud${NC}"
        echo ""
        echo "Possible issues:"
        echo "  • Fingerprint not set in config"
        echo "  • API key not uploaded to Oracle Cloud"
        echo "  • Network connectivity issues"
        echo ""
        echo "Debug with: oci iam region list --debug"
    fi
}

# Main installation flow
main() {
    detect_os
    check_existing

    echo "Select installation method:"
    echo "  1. Install with pip (recommended)"
    echo "  2. Use official installer"
    echo "  3. Skip installation (already installed)"
    echo ""
    read -p "Choice (1-3): " CHOICE

    case $CHOICE in
        1)
            install_with_pip
            ;;
        2)
            install_official
            ;;
        3)
            echo "Skipping installation"
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac

    # Configure
    configure_oci

    # Test connection
    test_connection

    echo ""
    echo "=== Setup Complete ==="
    echo ""
    echo "Next steps:"
    echo "  1. Upload API public key to Oracle Cloud Console"
    echo "  2. Add fingerprint to ~/.oci/config and .env"
    echo "  3. Run: ./provision_oracle_vms.py"
    echo ""
    echo "Quick test: oci iam region list"
    echo ""
}

# Run main
main