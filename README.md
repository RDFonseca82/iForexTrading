# iForexTrading

Bot para utilizar com a plataforma iForex.app


# Instalar

curl -fsSL https://raw.githubusercontent.com/RDFonseca82/iForexTrading/main/install.sh -o install.sh

chmod +x install.sh

sudo ./install.sh 

# Update

curl -fsSL https://raw.githubusercontent.com/RDFonseca82/iForexTrading/main/update.sh -o update.sh

chmod +x update.sh

sudo ./update.sh

# Servoço
systemctl status iforextrading

systemctl start iforextrading

systemctl stop iforextrading


# JSON Cliente exemplo

{
  "IDCliente": 12,
  "TipoMoeda": "BTCUSDT",
  "LotSize": 0.01,
  "StopLoss": 0.4,
  "TakeProfit": 0.06,
  "BotActive": 1,
  "Corretora": "Bybit",
  "CorretoraClientAPIKey": "API_KEY_AQUI",
  "CorretoraClientAPISecret": "API_SECRET_AQUI",
  "BybitEnvironment": "testnet"
}


# Corretora

{
  "Corretora": "bybit" | "binance",
  "CorretoraClientAPIKey": "...",
  "CorretoraClientAPISecret": "...",
  "BybitEnvironment": "testnet" | "real"
}

