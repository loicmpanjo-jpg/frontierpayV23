#!/bin/bash
set -e

echo "🔑 Génération des clés JWT RS256..."

mkdir -p keys

# Vérifier si openssl est installé
if ! command -v openssl &> /dev/null; then
    echo "❌ OpenSSL non trouvé. Installation..."
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y openssl
    elif command -v apk &> /dev/null; then
        apk add --no-cache openssl
    elif command -v brew &> /dev/null; then
        brew install openssl
    else
        echo "❌ Impossible d'installer OpenSSL automatiquement"
        exit 1
    fi
fi

# Générer les clés
openssl genrsa -out keys/jwt-private.pem 2048
openssl rsa -in keys/jwt-private.pem -pubout -out keys/jwt-public.pem

echo "✅ Clés JWT générées avec succès :"
ls -la keys/
