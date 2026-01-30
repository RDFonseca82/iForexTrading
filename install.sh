#!/bin/bash

APP_DIR="/opt/iForexTrading"
SERVICE_NAME="iforextrading"

echo "📥 A instalar iForexTrading..."

# Dependências
apt update
apt install -y python3 python3-pip git

# Clone ou update
if [ -d "$APP_DIR/.git" ]; then
    echo "🔄 Repositório já existe, a atualizar..."
    cd $APP_DIR || exit 1
    git pull
else
    echo "📦 A clonar repositório..."
    git clone https://github.com/RDFonseca82/iForexTrading.git $APP_DIR
    cd $APP_DIR || exit 1
fi

# Python deps
pip3 install -r requirements.txt

# Criar serviço systemd
cat <<EOF >/etc/systemd/system/$SERVICE_NAME.service
[Unit]
Description=iForexTrading Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $APP_DIR/main.py
Restart=always
RestartSec=5
User=root
WorkingDirectory=$APP_DIR

[Install]
WantedBy=multi-user.target
EOF

# Ativar serviço
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl restart $SERVICE_NAME

echo "✅ iForexTrading instalado e em execução"
