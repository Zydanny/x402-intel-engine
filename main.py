import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from engine import get_tier1_pulse, get_tier2_depth, get_tier3_signal

# Official x402 Server SDK Components
from x402.server import x402ResourceServer
from x402.http import HTTPFacilitatorClient, FacilitatorConfig, PaymentOption
from x402.http.types import RouteConfig
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.mechanisms.evm.exact import ExactEvmServerScheme

load_dotenv()

PAY_TO_ADDRESS = os.getenv("PAYMENT_RECEIVER_ADDRESS", "0xYourWalletAddressHere")
NETWORK = os.getenv("PAYMENT_NETWORK", "eip155:8453")
FACILITATOR_URL = os.getenv("FACILITATOR_URL", "https://x402.org/facilitator")

app = FastAPI(
    title="SuperZydan Agent Market Intelligence API",
    description="Multi-tier low-latency on-chain market intelligence for autonomous agents.",
    version="1.0.0"
)

# 1. Define x402 pricing per route
routes = {
    "GET /v1/intel/pulse/*": RouteConfig(
        accepts=PaymentOption(
            scheme="exact",
            network=NETWORK,
            pay_to=PAY_TO_ADDRESS,
            price="$0.01"
        ),
        description="Tier 1: 5m Buy/Sell volume momentum score"
    ),
    "GET /v1/intel/depth/*": RouteConfig(
        accepts=PaymentOption(
            scheme="exact",
            network=NETWORK,
            pay_to=PAY_TO_ADDRESS,
            price="$0.05"
        ),
        description="Tier 2: Liquidity depth, pool slippage, and wash-trading audit"
    ),
    "GET /v1/intel/signal/*": RouteConfig(
        accepts=PaymentOption(
            scheme="exact",
            network=NETWORK,
            pay_to=PAY_TO_ADDRESS,
            price="$0.10"
        ),
        description="Tier 3: Full composite execution signal and DEX route recommendation"
    )
}

# 2. Attach Facilitator & register Base EVM Server Scheme
facilitator_config = FacilitatorConfig(url=FACILITATOR_URL)
facilitator_client = HTTPFacilitatorClient(facilitator_config)
resource_server = x402ResourceServer(facilitator_client)
resource_server.register(NETWORK, ExactEvmServerScheme())

# 3. Add ASGI middleware
app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=resource_server)

# --- PUBLIC STATUS ENDPOINT ($0) ---
@app.get("/")
async def root():
    return {
        "status": "online",
        "endpoints": {
            "/v1/intel/pulse/{token}": "$0.01 USDC",
            "/v1/intel/depth/{token}": "$0.05 USDC",
            "/v1/intel/signal/{token}": "$0.10 USDC"
        }
    }

# --- TIER 1 ROUTE ---
@app.get("/v1/intel/pulse/{token}")
async def pulse(token: str):
    data = get_tier1_pulse(token)
    if not data or "error" in data:
        raise HTTPException(status_code=404, detail="Token data unavailable")
    return data

# --- TIER 2 ROUTE ---
@app.get("/v1/intel/depth/{token}")
async def depth(token: str):
    data = get_tier2_depth(token)
    if not data or "error" in data:
        raise HTTPException(status_code=404, detail="Token data unavailable")
    return data

# --- TIER 3 ROUTE ---
@app.get("/v1/intel/signal/{token}")
async def signal(token: str):
    data = get_tier3_signal(token)
    if not data or "error" in data:
        raise HTTPException(status_code=404, detail="Token data unavailable")
    return data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)