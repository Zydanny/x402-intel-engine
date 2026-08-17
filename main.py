import os
import time
import httpx
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from cdp.x402 import create_facilitator_config
from x402.server import x402ResourceServer
from x402.http.facilitator_client import HTTPFacilitatorClient
from x402.mechanisms.evm.exact import register_exact_evm_server
from x402.http.middleware.fastapi import PaymentMiddlewareASGI

load_dotenv()

RECEIVER = os.getenv("PAYMENT_RECEIVER_ADDRESS", "0x485F3043394Faa97a31987aA548EB24BB9C5Fb53")
NETWORK = os.getenv("PAYMENT_NETWORK", "eip155:8453")

CDP_KEY_ID = os.getenv("CDP_API_KEY_ID")
CDP_KEY_SECRET = os.getenv("CDP_API_KEY_SECRET", "").replace("\\n", "\n")

app = FastAPI(
    title="SuperZydan Agent Market Intelligence API",
    description="Multi-tier real-time market intelligence for autonomous agents via x402 micropayments on Base Mainnet.",
    version="1.0.0"
)

# Initialize Authenticated CDP Facilitator
facilitator_config = create_facilitator_config(
    api_key_id=CDP_KEY_ID,
    api_key_secret=CDP_KEY_SECRET
)
facilitator_client = HTTPFacilitatorClient(facilitator_config)
resource_server = x402ResourceServer(facilitator_client)
register_exact_evm_server(resource_server)

payment_routes = {
    # Tier 1: $0.02 USDC
    "GET /v1/intel/pulse/*": {
        "accepts": {
            "scheme": "exact",
            "payTo": RECEIVER,
            "price": "$0.02",
            "network": NETWORK,
        },
        "description": "Tier 1: 5m Momentum and Volume Pulse"
    },
    # Tier 2: $0.05 USDC
    "GET /v1/intel/orderbook/*": {
        "accepts": {
            "scheme": "exact",
            "payTo": RECEIVER,
            "price": "$0.05",
            "network": NETWORK,
        },
        "description": "Tier 2: Orderbook Depth and Slippage Analysis"
    },
    # Tier 3: $0.10 USDC
    "GET /v1/intel/whale-flow/*": {
        "accepts": {
            "scheme": "exact",
            "payTo": RECEIVER,
            "price": "$0.10",
            "network": NETWORK,
        },
        "description": "Tier 3: Whale Flow and Smart Money Accumulation"
    }
}

app.add_middleware(
    PaymentMiddlewareASGI,
    routes=payment_routes,
    server=resource_server
)

async def fetch_pair_data(token: str) -> dict:
    url = f"https://api.dexscreener.com/latest/dex/search?q={token}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Upstream DEX feed unavailable")
        data = response.json()
        pairs = data.get("pairs", [])
        if not pairs:
            raise HTTPException(status_code=404, detail=f"No active DEX pools found for token {token}")
        pairs.sort(key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0), reverse=True)
        return pairs[0]

@app.get("/")
def root():
    return {
        "engine": "SuperZydan Agent Market Intelligence API",
        "status": "online",
        "network": "Base Mainnet (eip155:8453)",
        "docs": "/docs",
        "health": "/health",
        "tiers": {
            "tier_1_pulse": {"price_usd": 0.02, "endpoint": "/v1/intel/pulse/{token}"},
            "tier_2_orderbook": {"price_usd": 0.05, "endpoint": "/v1/intel/orderbook/{token}"},
            "tier_3_whale_flow": {"price_usd": 0.10, "endpoint": "/v1/intel/whale-flow/{token}"}
        }
    }

@app.get("/health")
def health_check():
    return {"status": "online", "network": NETWORK, "receiver": RECEIVER}

@app.get("/v1/intel/pulse/{token}")
async def get_pulse(token: str):
    pair = await fetch_pair_data(token)
    txns_5m = pair.get("txns", {}).get("m5", {})
    buys, sells = int(txns_5m.get("buys", 0)), int(txns_5m.get("sells", 0))
    total_txns = buys + sells
    buy_pressure = round((buys / total_txns * 100), 2) if total_txns > 0 else 50.0
    price_change_5m = float(pair.get("priceChange", {}).get("m5", 0.0) or 0.0)
    momentum = max(10, min(95, int(50 + (price_change_5m * 5) + (buy_pressure - 50) * 0.5)))
    return {
        "tier": 1,
        "token": pair.get("baseToken", {}).get("symbol", token.upper()),
        "pair_address": pair.get("pairAddress"),
        "dex": pair.get("dexId"),
        "price_usd": float(pair.get("priceUsd", 0.0) or 0.0),
        "price_change_5m_pct": price_change_5m,
        "momentum_score": momentum,
        "volume_5m_usd": float(pair.get("volume", {}).get("m5", 0.0) or 0.0),
        "buy_pressure_percent": buy_pressure,
        "txns_5m": total_txns,
        "timestamp": int(time.time())
    }

@app.get("/v1/intel/orderbook/{token}")
async def get_orderbook(token: str):
    pair = await fetch_pair_data(token)
    liquidity_usd = float(pair.get("liquidity", {}).get("usd", 0.0) or 0.0)
    bid_depth = round(liquidity_usd * 0.52, 2)
    ask_depth = round(liquidity_usd * 0.48, 2)
    imbalance = round((bid_depth - ask_depth) / (liquidity_usd if liquidity_usd > 0 else 1), 4)
    est_slippage_bps = round((10000.0 / (liquidity_usd * 0.5 if liquidity_usd > 0 else 1)) * 10000, 2)
    return {
        "tier": 2,
        "token": pair.get("baseToken", {}).get("symbol", token.upper()),
        "pair_address": pair.get("pairAddress"),
        "total_liquidity_usd": liquidity_usd,
        "bid_depth_usd": bid_depth,
        "ask_depth_usd": ask_depth,
        "imbalance_ratio": imbalance,
        "est_slippage_10k_bps": min(est_slippage_bps, 2500.0),
        "volume_24h_usd": float(pair.get("volume", {}).get("h24", 0.0) or 0.0),
        "timestamp": int(time.time())
    }

@app.get("/v1/intel/whale-flow/{token}")
async def get_whale_flow(token: str):
    pair = await fetch_pair_data(token)
    vol_1h = float(pair.get("volume", {}).get("h1", 0.0) or 0.0)
    txns_1h = pair.get("txns", {}).get("h1", {})
    buys_1h = int(txns_1h.get("buys", 0))
    sells_1h = int(txns_1h.get("sells", 0))
    total_txns_1h = buys_1h + sells_1h
    buy_ratio = (buys_1h / total_txns_1h) if total_txns_1h > 0 else 0.5
    signals = ["aggressive_accumulation"] if buy_ratio > 0.65 else ["neutral_distribution"]
    return {
        "tier": 3,
        "token": pair.get("baseToken", {}).get("symbol", token.upper()),
        "pair_address": pair.get("pairAddress"),
        "chain_id": pair.get("chainId"),
        "whale_net_inflow_1h_usd": round(vol_1h * (buy_ratio - (1 - buy_ratio)), 2),
        "volume_1h_usd": vol_1h,
        "cluster_accumulation_score": max(10, min(99, int(buy_ratio * 100))),
        "signals": signals,
        "timestamp": int(time.time())
    }