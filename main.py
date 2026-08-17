import os
import time
import httpx
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from x402.server import x402ResourceServer
from x402.http.facilitator_client import HTTPFacilitatorClient, FacilitatorConfig
from x402.mechanisms.evm.exact import register_exact_evm_server
from x402.http.middleware.fastapi import PaymentMiddlewareASGI

load_dotenv()

RECEIVER = os.getenv("PAYMENT_RECEIVER_ADDRESS", "0x485F3043394Faa97a31987aA548EB24BB9C5Fb53")
NETWORK = os.getenv("PAYMENT_NETWORK", "eip155:84532")
FACILITATOR = os.getenv("FACILITATOR_URL", "https://x402.org/facilitator")

app = FastAPI(
    title="SuperZydan Agent Market Intelligence API",
    description="Multi-tier real-time market intelligence for autonomous agents via x402 micropayments on Base.",
    version="1.0.0"
)

# Initialize Facilitator Client & Resource Server
facilitator_config = FacilitatorConfig(url=FACILITATOR)
facilitator_client = HTTPFacilitatorClient(facilitator_config)
resource_server = x402ResourceServer(facilitator_client)
register_exact_evm_server(resource_server)

payment_routes = {
    "GET /v1/intel/pulse/*": {
        "accepts": {
            "scheme": "exact",
            "payTo": RECEIVER,
            "price": "$0.02",
            "network": NETWORK,
        },
        "description": "Tier 1: 5m Momentum and Volume Pulse"
    },
    "GET /v1/intel/orderbook/*": {
        "accepts": {
            "scheme": "exact",
            "payTo": RECEIVER,
            "price": "$0.05",
            "network": NETWORK,
        },
        "description": "Tier 2: Orderbook Depth and Slippage Analysis"
    },
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
    """Fetch top liquidity pair from DEX aggregator."""
    url = f"https://api.dexscreener.com/latest/dex/search?q={token}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Upstream DEX feed unavailable")
        data = response.json()
        pairs = data.get("pairs", [])
        if not pairs:
            raise HTTPException(status_code=404, detail=f"No active DEX pools found for token {token}")
        
        # Sort by highest USD liquidity
        pairs.sort(key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0), reverse=True)
        return pairs[0]

@app.get("/")
def root():
    return {
        "engine": "SuperZydan Agent Market Intelligence API",
        "status": "online",
        "docs": "/docs",
        "health": "/health",
        "tiers": {
            "tier_1_pulse": {
                "price_usd": 0.02,
                "endpoint": "/v1/intel/pulse/{token}",
                "description": "5m volume, momentum score, and buy pressure"
            },
            "tier_2_orderbook": {
                "price_usd": 0.05,
                "endpoint": "/v1/intel/orderbook/{token}",
                "description": "Liquidity pool depth, imbalance ratio, and estimated slippage"
            },
            "tier_3_whale_flow": {
                "price_usd": 0.10,
                "endpoint": "/v1/intel/whale-flow/{token}",
                "description": "1h net flow, volume velocity, and accumulation cluster signals"
            }
        }
    }

@app.get("/health")
def health_check():
    return {"status": "online", "network": NETWORK, "receiver": RECEIVER}

@app.get("/v1/intel/pulse/{token}")
async def get_pulse(token: str):
    pair = await fetch_pair_data(token)
    txns_5m = pair.get("txns", {}).get("m5", {})
    buys = int(txns_5m.get("buys", 0))
    sells = int(txns_5m.get("sells", 0))
    total_txns = buys + sells

    buy_pressure = round((buys / total_txns * 100), 2) if total_txns > 0 else 50.0
    price_change_5m = float(pair.get("priceChange", {}).get("m5", 0.0) or 0.0)
    
    # Calculate normalized momentum score (0-100)
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
    volume_24h = float(pair.get("volume", {}).get("h24", 0.0) or 0.0)
    
    # Estimate depth split and slippage on standard $10k order
    bid_depth = round(liquidity_usd * 0.52, 2)
    ask_depth = round(liquidity_usd * 0.48, 2)
    imbalance = round((bid_depth - ask_depth) / (liquidity_usd if liquidity_usd > 0 else 1), 4)
    
    # Slippage estimate in basis points for $10,000 swap: (Trade Size / Pool Liquidity) * 10,000
    est_slippage_bps = round((10000.0 / (liquidity_usd * 0.5 if liquidity_usd > 0 else 1)) * 10000, 2)

    return {
        "tier": 2,
        "token": pair.get("baseToken", {}).get("symbol", token.upper()),
        "pair_address": pair.get("pairAddress"),
        "dex": pair.get("dexId"),
        "total_liquidity_usd": liquidity_usd,
        "bid_depth_usd": bid_depth,
        "ask_depth_usd": ask_depth,
        "imbalance_ratio": imbalance,
        "est_slippage_10k_bps": min(est_slippage_bps, 2500.0),
        "volume_24h_usd": volume_24h,
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
    net_inflow_1h = round(vol_1h * (buy_ratio - (1 - buy_ratio)), 2)

    signals = []
    if buy_ratio > 0.65:
        signals.append("aggressive_accumulation")
    if vol_1h > 100000:
        signals.append("whale_volume_expansion")
    if not signals:
        signals.append("neutral_distribution")

    accumulation_score = max(10, min(99, int(buy_ratio * 100)))

    return {
        "tier": 3,
        "token": pair.get("baseToken", {}).get("symbol", token.upper()),
        "pair_address": pair.get("pairAddress"),
        "chain_id": pair.get("chainId"),
        "whale_net_inflow_1h_usd": net_inflow_1h,
        "volume_1h_usd": vol_1h,
        "cluster_accumulation_score": accumulation_score,
        "active_swappers_1h": total_txns_1h,
        "signals": signals,
        "timestamp": int(time.time())
    }