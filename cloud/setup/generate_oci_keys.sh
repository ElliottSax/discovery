#!/bin/bash
#
# Generate Oracle Cloud Infrastructure (OCI) API Keys
# This script creates API key pairs for Oracle Cloud authentication
#

set -e

echo "======================================================================="
echo "Oracle Cloud API Key Generation"
echo "======================================================================="
echo ""

# Configuration
OCI_DIR="$HOME/.oci"
KEY_NAME="oci_api_key"

# Create .oci directory if it doesn't exist
echo "Creating Oracle Cloud configuration directory..."
mkdir -p "$OCI_DIR"
chmod 700 "$OCI_DIR"

# Check if keys already exist
if [ -f "$OCI_DIR/${KEY_NAME}.pem" ]; then
    echo ""
    echo "⚠️  WARNING: API keys already exist at $OCI_DIR/${KEY_NAME}.pem"
    read -p "Do you want to overwrite? (yes/no): " OVERWRITE
    if [ "$OVERWRITE" != "yes" ]; then
        echo "Using existing keys..."
        echo ""
    else
        echo "Backing up existing keys..."
        mv "$OCI_DIR/${KEY_NAME}.pem" "$OCI_DIR/${KEY_NAME}.pem.backup"
        mv "$OCI_DIR/${KEY_NAME}_public.pem" "$OCI_DIR/${KEY_NAME}_public.pem.backup"
        echo "Old keys backed up with .backup extension"
        echo ""
    fi
fi

# Generate new keys if needed
if [ ! -f "$OCI_DIR/${KEY_NAME}.pem" ]; then
    echo "Generating new API key pair..."

    # Generate private key
    openssl genrsa -out "$OCI_DIR/${KEY_NAME}.pem" 2048

    # Generate public key
    openssl rsa -pubout -in "$OCI_DIR/${KEY_NAME}.pem" -out "$OCI_DIR/${KEY_NAME}_public.pem"

    # Set proper permissions
    chmod 600 "$OCI_DIR/${KEY_NAME}.pem"
    chmod 644 "$OCI_DIR/${KEY_NAME}_public.pem"

    echo "✅ Keys generated successfully!"
    echo ""
fi

# Display public key
echo "======================================================================="
echo "PUBLIC KEY (Copy this to Oracle Cloud Console)"
echo "======================================================================="
cat "$OCI_DIR/${KEY_NAME}_public.pem"
echo "======================================================================="
echo ""

# Instructions
echo "NEXT STEPS:"
echo ""
echo "1. Log in to Oracle Cloud Console: https://cloud.oracle.com"
echo "2. Click Profile menu (top right) → User Settings"
echo "3. Under Resources (left sidebar), click API Keys"
echo "4. Click 'Add API Key'"
echo "5. Select 'Paste Public Key'"
echo "6. Paste the PUBLIC KEY shown above"
echo "7. Click 'Add'"
echo "8. IMPORTANT: Copy the FINGERPRINT shown (format: aa:bb:cc:dd:...)"
echo ""
echo "Files created:"
echo "  Private key: $OCI_DIR/${KEY_NAME}.pem"
echo "  Public key:  $OCI_DIR/${KEY_NAME}_public.pem"
echo ""
echo "Keep your private key secure! Never share it or commit it to git."
echo ""

# Offer to display configuration
echo "After adding the key to Oracle Cloud, you'll need to update your .env file."
echo "Press Enter when you have the fingerprint from Oracle Cloud..."
read

# Get user's Oracle Cloud details
echo ""
echo "Let's configure your Oracle Cloud connection."
echo "You can find these values in the Oracle Cloud Console."
echo ""

# Get fingerprint
read -p "Enter your API key FINGERPRINT (format: aa:bb:cc:...): " FINGERPRINT

# Show configuration
echo ""
echo "======================================================================="
echo "Add these to your .env file:"
echo "======================================================================="
echo ""
echo "# Oracle Cloud Configuration"
echo "ORACLE_USER_OCID=ocid1.user.oc1..aaaaaaaa74qquxlbn7ky5lpcfkt2akeemtn4v2gd7kdc52dve7mx7kxbdziq"
echo "ORACLE_TENANCY_OCID=ocid1.tenancy.oc1..aaaaaaaa2ktu74gnhxcctwnk65ntpj6gfb53ofanbz2ram3jkm62ke5ekpsa"
echo "ORACLE_REGION=us-chicago-1"
echo "ORACLE_FINGERPRINT=$FINGERPRINT"
echo "ORACLE_PRIVATE_KEY_PATH=$OCI_DIR/${KEY_NAME}.pem"
echo ""
echo "======================================================================="
echo ""

echo "✅ Oracle Cloud API key setup complete!"
echo ""
echo "Next step: Create and configure your Oracle Cloud VMs"
echo "Run: ./provision_oracle_vms.sh"
echo ""