#!/bin/bash

APP_DIR="/opt/iForexTrading"
SERVICE_NAME="iforextrading"
PYTHON_BIN="/usr/bin/python3"

echo "📥 A instalar iForexTrading (modo venv)..."

apt update
apt install -y python3 python3-venv python3-pip git

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

# Criar venv se não existir
if [ ! -d "$APP_DIR/venv" ]; then
    echo "🐍 A criar virtualenv..."
    $PYTHON_BIN -m venv venv
fi

# Instalar dependências no venv
echo "📦 A instalar dependências Python..."
$APP_DIR/venv/bin/pip install --upgrade pip
$APP_DIR/venv/bin/pip install -r requirements.txt

# Criar serviço systemd
cat <<EOF >/etc/systemd/system/$SERVICE_NAME.service
[Unit]
Description=iForexTrading Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/main.py
Restart=always
RestartSec=5
User=root
WorkingDirectory=$APP_DIR
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl restart $SERVICE_NAME

echo "✅ iForexTrading instalado corretamente (venv)"
