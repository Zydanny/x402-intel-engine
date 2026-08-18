import os
import json
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from eth_account import Account
from x402.client import x402Client
from x402.http.clients.httpx import x402HttpxClient
from x402.mechanisms.evm.exact import register_exact_evm_client

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "https://x402-intel-engine-production.up.railway.app")
AGENT_PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")

# Initialize MCP Server
mcp = FastMCP("SuperZydan Market Intelligence")

def get_authenticated_client() -> httpx.Client:
    """Builds an HTTP client capable of automatically signing x402 micropayments."""
    if not AGENT_PRIVATE_KEY:
        # Fallback to standard client (will return 402 payload if unpaid)
        return httpx.Client(timeout=15.0)
    
    account = Account.from_key(AGENT_PRIVATE_KEY)
    client = x402Client()
    register_exact_evm_client(client, account)
    return x402HttpxClient(client=httpx.Client(timeout=15.0), x402_client=client)

@mcp.tool()
def get_market_pulse(token: str) -> str:
    """
    Tier 1 ($0.02 USDC): Fetches real-time 5m momentum, buy/sell transaction count,
    volume, and buy-pressure score for any cryptocurrency or DEX token.
    """
    url = f"{API_BASE_URL}/v1/intel/pulse/{token}"
    with get_authenticated_client() as client:
        res = client.get(url)
        return json.dumps(res.json(), indent=2)

@mcp.tool()
def get_orderbook_depth(token: str) -> str:
    """
    Tier 2 ($0.05 USDC): Fetches simulated orderbook bid/ask depth, liquidity imbalance,
    and estimated slippage (in bps) for $10k trades.
    """
    url = f"{API_BASE_URL}/v1/intel/orderbook/{token}"
    with get_authenticated_client() as client:
        res = client.get(url)
        return json.dumps(res.json(), indent=2)

@mcp.tool()
def get_whale_flow(token: str) -> str:
    """
    Tier 3 ($0.10 USDC): Fetches 1h smart money accumulation, net whale inflow (USD),
    and cluster accumulation confidence signals.
    """
    url = f"{API_BASE_URL}/v1/intel/whale-flow/{token}"
    with get_authenticated_client() as client:
        res = client.get(url)
        return json.dumps(res.json(), indent=2)

if __name__ == "__main__":
    mcp.run()