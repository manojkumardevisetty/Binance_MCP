module.exports = {
  apps: [{
    name: "binance-mcp",
    script: "/opt/binance-mcp/venv/bin/python",
    args: "/opt/binance-mcp/src/server_http.py",
    cwd: "/opt/binance-mcp",
    env: {
      JWT_SECRET: "40bdbe0528ac11864ff73defc5913ec7a44b0324530fdd752b98e5c64fcaf688",
      BINANCE_TESTNET: "true",
      DRY_RUN: "false",
      MAX_LEVERAGE: "100",
      MAX_NOTIONAL_USDT: "50000",
      DAILY_LOSS_LIMIT_USDT: "20000",
      SYMBOL_WHITELIST: "BTCUSDT,ETHUSDT,SOLUSDT,AVAXUSDT",
      PORT: "8765",
      HOST: "127.0.0.1"
    },
    log_file: "/opt/binance-mcp/logs/combined.log",
    error_file: "/opt/binance-mcp/logs/error.log",
    out_file: "/opt/binance-mcp/logs/out.log",
    time: true,
    restart_delay: 5000,
    max_restarts: 10
  }]
}
