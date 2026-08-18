# x402 DEX Market Intelligence API & MCP Server

Real-time DEX token momentum, liquidity health, and whale flow monitoring on Base Mainnet gated with gasless **x402 (EIP-3009)** micropayments.

- **Interactive API Docs:** https://x402-intel-engine-production.up.railway.app/docs
- **OpenAPI Schema:** https://x402-intel-engine-production.up.railway.app/openapi.json
- **Settlement Chain:** Base Mainnet (`8453`)
- **Asset:** USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)

---

## Available Endpoints & MCP Tools

| Endpoint | Price (USDC) | Description |
| :--- | :--- | :--- |
| `GET /v1/intel/pulse/{token}` | `$0.02` | 5m volume, buy pressure, momentum score |
| `GET /v1/intel/orderbook/{token}` | `$0.05` | DEX liquidity depth & turnover ratio |
| `GET /v1/intel/whale-flow/{token}` | `$0.10` | 1h whale accumulation & distribution signals |

---

## Quickstart: MCP Setup (Claude Desktop / Cursor)

Add the server to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "x402-dex-intel": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "AGENT_PRIVATE_KEY": "0x_YOUR_FUNDED_BASE_WALLET_PRIVATE_KEY"
      }
    }
  }
}