#!/bin/bash

echo "🔐 Creating Self-Signed Code Signing Certificate"
echo "==============================================="
echo ""

# Create certificate using security command
echo "Creating certificate for Barbell Logic Turnkey Coach Tools..."

cat << 'EOF' > /tmp/cert.conf
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = Oklahoma
L = Claremore
O = Barbell Logic
OU = Software Development
CN = Turnkey Coach Tools Code Signing
emailAddress = kschudt@barbell-logic.com

[v3_req]
keyUsage = digitalSignature
extendedKeyUsage = codeSigning
basicConstraints = CA:false
EOF

# Generate key and certificate
openssl genrsa -out /tmp/codesign.key 2048
openssl req -new -x509 -key /tmp/codesign.key -out /tmp/codesign.crt -days 365 -config /tmp/cert.conf

# Convert to PKCS12
openssl pkcs12 -export -out /tmp/codesign.p12 -inkey /tmp/codesign.key -in /tmp/codesign.crt -passout pass:

# Import to keychain
echo ""
echo "Importing certificate to keychain..."
security delete-certificate -c "Turnkey Coach Tools Code Signing" 2>/dev/null || true
security import /tmp/codesign.p12 -k ~/Library/Keychains/login.keychain-db -T /usr/bin/codesign -P ""

# Verify
echo ""
echo "Checking for signing identities..."
security find-identity -v -p codesigning

# Clean up
rm -f /tmp/cert.conf /tmp/codesign.*

echo ""
echo "✅ Certificate creation complete!"
echo ""
echo "To sign your app, use:"
echo 'codesign --force --sign "Turnkey Coach Tools Code Signing" YourApp.app'