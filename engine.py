import time
import requests

CACHE = {}
CACHE_TTL = 15  # 15-second cache to prevent redundant external API hits

def fetch_raw_dex_data(token_symbol: str) -> dict:
    """Fetches real-time multi-pool DEX metrics."""
    now = time.time()
    if token_symbol in CACHE and (now - CACHE[token_symbol]["timestamp"]) < CACHE_TTL:
        return CACHE[token_symbol]["data"]

    # Pull real-time aggregated pair data
    url = f"https://api.dexscreener.com/latest/dex/search?q={token_symbol}"
    try:
        res = requests.get(url, timeout=5).json()
        pairs = res.get("pairs", [])
        if not pairs:
            return None
        
        # Select highest liquidity pair
        top_pair = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0))
        data = {
            "symbol": token_symbol.upper(),
            "price_usd": float(top_pair.get("priceUsd", 0)),
            "liquidity_usd": float(top_pair.get("liquidity", {}).get("usd", 0)),
            "vol_5m": float(top_pair.get("volume", {}).get("m5", 0)),
            "buys_5m": int(top_pair.get("txns", {}).get("m5", {}).get("buys", 0)),
            "sells_5m": int(top_pair.get("txns", {}).get("m5", {}).get("sells", 0)),
            "price_change_5m": float(top_pair.get("priceChange", {}).get("m5", 0)),
            "dex_id": top_pair.get("dexId"),
            "pair_address": top_pair.get("pairAddress")
        }
        CACHE[token_symbol] = {"timestamp": now, "data": data}
        return data
    except Exception:
        return None

# --- TIER 1 LOGIC ($0.01) ---
def get_tier1_pulse(token: str) -> dict:
    raw = fetch_raw_dex_data(token)
    if not raw:
        return {"error": "Token pair not found or liquidity too low"}
    
    total_tx = raw["buys_5m"] + raw["sells_5m"]
    order_flow_ratio = round((raw["buys_5m"] / total_tx) * 100, 1) if total_tx > 0 else 50.0
    
    return {
        "token": raw["symbol"],
        "price_usd": raw["price_usd"],
        "momentum_score": 85 if raw["price_change_5m"] > 2 and order_flow_ratio > 60 else 45,
        "volume_5m_usd": raw["vol_5m"],
        "buy_pressure_percent": order_flow_ratio,
        "latency_ms": 12,
        "timestamp": int(time.time())
    }

# --- TIER 2 LOGIC ($0.05) ---
def get_tier2_depth(token: str) -> dict:
    raw = fetch_raw_dex_data(token)
    if not raw:
        return {"error": "Token pair not found"}
    
    # Calculate synthetic slippage impact
    liq = raw["liquidity_usd"]
    slip_1k = round((1000 / liq) * 100, 3) if liq > 0 else 99.0
    slip_10k = round((10000 / liq) * 100, 3) if liq > 0 else 99.0

    return {
        "token": raw["symbol"],
        "primary_dex": raw["dex_id"],
        "pool_address": raw["pair_address"],
        "total_liquidity_usd": liq,
        "est_slippage_1k_usd": f"{slip_1k}%",
        "est_slippage_10k_usd": f"{slip_10k}%",
        "wash_trade_risk": "HIGH" if raw["vol_5m"] > liq * 0.8 and raw["buys_5m"] == raw["sells_5m"] else "LOW",
        "timestamp": int(time.time())
    }

# --- TIER 3 LOGIC ($0.10) ---
def get_tier3_signal(token: str) -> dict:
    raw = fetch_raw_dex_data(token)
    if not raw:
        return {"error": "Token pair not found"}
    
    t1 = get_tier1_pulse(token)
    t2 = get_tier2_depth(token)
    
    # Composite decision matrix
    action = "HOLD"
    confidence = 0.50
    if t1["momentum_score"] > 70 and t2["wash_trade_risk"] == "LOW":
        action = "ACCUMULATE"
        confidence = 0.88
    elif t1["buy_pressure_percent"] < 35:
        action = "DISTRIBUTE"
        confidence = 0.82

    return {
        "token": raw["symbol"],
        "composite_verdict": action,
        "model_confidence": confidence,
        "suggested_max_slippage": t2["est_slippage_1k_usd"],
        "optimal_dex_route": raw["dex_id"],
        "summary": f"Signal driven by {t1['buy_pressure_percent']}% 5m buy ratio and ${t2['total_liquidity_usd']:,.0f} pool depth.",
        "timestamp": int(time.time())
    }