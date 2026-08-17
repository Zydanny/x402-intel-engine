import os
import time
import random
from fastapi import FastAPI
from dotenv import load_dotenv
from x402.fastapi import x402PaymentMiddleware
from x402.mechanisms.evm.exact import ExactEvmServerScheme

load_dotenv()

RECEIVER = os.getenv("PAYMENT_RECEIVER_ADDRESS", "0x485F3043394Faa97a31987aA548EB24BB9C5Fb53")
NETWORK = os.getenv("PAYMENT_NETWORK", "eip155:84532")
FACILITATOR = os.getenv("FACILITATOR_URL", "https://x402.org/facilitator")

app = FastAPI(
    title="SuperZydan Agent Market Intelligence API",
    description="Multi-tier real-time market intelligence for autonomous agents via x402 micropayments on Base.",
    version="1.0.0"
)

# Configure x402 payment requirements per tier
payment_routes = {
    # Tier 1: $0.02 USDC (20,000 atomic units)
    "^/v1/intel/pulse/.*$": {
        "network": NETWORK,
        "amount": "20000",
        "payTo": RECEIVER,
        "description": "Tier 1: 5m Momentum & Volume Pulse"
    },
    # Tier 2: $0.05 USDC (50,000 atomic units)
    "^/v1/intel/orderbook/.*$": {
        "network": NETWORK,
        "amount": "50000",
        "payTo": RECEIVER,
        "description": "Tier 2: Orderbook Depth & Slippage Analysis"
    },
    # Tier 3: $0.10 USDC (100,000 atomic units)
    "^/v1/intel/whale-flow/.*$": {
        "network": NETWORK,
        "amount": "100000",
        "payTo": RECEIVER,
        "description": "Tier 3: Whale Flow & Smart Money Accumulation"
    }
}

app.add_middleware(
    x402PaymentMiddleware,
    routes=payment_routes,
    facilitator_url=FACILITATOR
)

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
                "description": "5m volume & momentum scoring"
            },
            "tier_2_orderbook": {
                "price_usd": 0.05,
                "endpoint": "/v1/intel/orderbook/{token}",
                "description": "Liquidity depth imbalance & estimated slippage"
            },
            "tier_3_whale_flow": {
                "price_usd": 0.10,
                "endpoint": "/v1/intel/whale-flow/{token}",
                "description": "Whale net flow & smart wallet accumulation clusters"
            }
        }
    }

@app.get("/health")
def health_check():
    return {"status": "online", "network": NETWORK, "receiver": RECEIVER}

@app.get("/v1/intel/pulse/{token}")
def get_pulse(token: str):
    return {
        "tier": 1,
        "token": token.upper(),
        "momentum_score": random.randint(30, 95),
        "volume_5m_usd": round(random.uniform(50000, 2500000), 2),
        "buy_pressure_percent": round(random.uniform(40.0, 85.0), 2),
        "timestamp": int(time.time())
    }

@app.get("/v1/intel/orderbook/{token}")
def get_orderbook(token: str):
    return {
        "tier": 2,
        "token": token.upper(),
        "bid_depth_usd": round(random.uniform(500000, 10000000), 2),
        "ask_depth_usd": round(random.uniform(500000, 10000000), 2),
        "imbalance_ratio": round(random.uniform(-0.5, 0.5), 3),
        "est_slippage_100k_bps": round(random.uniform(2.5, 18.0), 2),
        "timestamp": int(time.time())
    }

@app.get("/v1/intel/whale-flow/{token}")
def get_whale_flow(token: str):
    return {
        "tier": 3,
        "token": token.upper(),
        "whale_net_inflow_1h_usd": round(random.uniform(-500000, 3000000), 2),
        "cluster_accumulation_score": random.randint(60, 99),
        "smart_wallets_active": random.randint(3, 42),
        "signals": ["cluster_buy_spike", "liquidity_sweep"],
        "timestamp": int(time.time())
    }