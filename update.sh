#!/bin/bash

APP_DIR="/opt/iForexTrading"
SERVICE_NAME="iforextrading"

cd $APP_DIR || exit 1

echo "🔄 A verificar atualizações..."
git fetch origin main

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "⬇️ Atualização encontrada, a aplicar..."
    git pull
    systemctl restart $SERVICE_NAME
    echo "✅ Atualizado com sucesso"
else
    echo "✔ Sem alterações"
fi
