# iForexTrading

Instalar

chmod +x install.sh

curl -fsSL https://raw.githubusercontent.com/RDFonseca82/iForexTrading/main/install.sh | bash





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

