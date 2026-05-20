#!/bin/bash
# Generate self-signed SSL certificate for hospital intranet deployment.
# In production, replace with CA-signed certificate.

set -e

CERT_DIR="$(dirname "$0")/ssl"
mkdir -p "$CERT_DIR"

echo "Generating self-signed SSL certificate..."

openssl req -x509 -nodes \
    -days 3650 \
    -newkey rsa:4096 \
    -keyout "$CERT_DIR/okbox.key" \
    -out "$CERT_DIR/okbox.crt" \
    -subj "/C=CN/ST=State/L=City/O=Hospital/OU=IT/CN=okbox.local" \
    -addext "subjectAltName=DNS:okbox.local,DNS:*.okbox.local,IP:127.0.0.1"

echo "Certificate generated:"
echo "  Key:  $CERT_DIR/okbox.key"
echo "  Cert: $CERT_DIR/okbox.crt"
echo ""
echo "Add to deploy/.env: NGINX_SSL_CERT=./nginx/ssl/okbox.crt"
echo "                     NGINX_SSL_KEY=./nginx/ssl/okbox.key"
