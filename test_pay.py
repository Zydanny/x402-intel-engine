import os
import json
import base64
import requests
from dotenv import load_dotenv
from eth_account import Account
from eth_account.messages import encode_typed_data

load_dotenv()

# Private key for buyer agent (from .env or test fallback)
PRIVATE_KEY = os.getenv("BUYER_PRIVATE_KEY")
if not PRIVATE_KEY:
    # Ephemeral test key if not set in .env
    acc = Account.create()
    PRIVATE_KEY = acc.key.hex()
    print(f"[!] Generated ephemeral test key: {acc.address}")

account = Account.from_key(PRIVATE_KEY)
print(f"[*] Buyer Agent Address: {account.address}")

TARGET_URL = "https://x402-intel-engine-production.up.railway.app/v1/intel/pulse/SOL"

# Step 1: Send initial request to trigger 402 challenge
print(f"[*] Requesting: {TARGET_URL}")
res = requests.get(TARGET_URL)

if res.status_code == 200:
    print("[+] Endpoint returned 200 without payment:")
    print(json.dumps(res.json(), indent=2))
    exit(0)

if res.status_code != 402:
    print(f"[-] Unexpected status code: {res.status_code}")
    print(res.text)
    exit(1)

# Step 2: Parse payment requirements
header_val = res.headers.get("payment-required") or res.headers.get("PAYMENT-REQUIRED")
if not header_val:
    print("[-] Missing payment-required header in 402 response")
    exit(1)

reqs = json.loads(base64.b64decode(header_val).decode("utf-8"))
accept = reqs["accepts"][0]
print(f"[*] Payment Challenge: {accept['amount']} atomic units to {accept['payTo']} on {accept['network']}")

# Step 3: Sign EIP-712 payment authorization
chain_id = int(accept["network"].split(":")[-1])
domain = {
    "name": accept["extra"].get("name", "USDC"),
    "version": accept["extra"].get("version", "2"),
    "chainId": chain_id,
    "verifyingContract": accept["asset"]
}

types = {
    "TransferWithAuthorization": [
        {"name": "from", "type": "address"},
        {"name": "to", "type": "address"},
        {"name": "value", "type": "uint256"},
        {"name": "validAfter", "type": "uint256"},
        {"name": "validBefore", "type": "uint256"},
        {"name": "nonce", "type": "bytes32"}
    ]
}

import time, secrets
valid_after = 0
valid_before = int(time.time()) + int(accept.get("maxTimeoutSeconds", 300))
nonce = "0x" + secrets.token_hex(32)

message = {
    "from": account.address,
    "to": accept["payTo"],
    "value": int(accept["amount"]),
    "validAfter": valid_after,
    "validBefore": valid_before,
    "nonce": nonce
}

signable = encode_typed_data(domain_data=domain, message_types=types, message_data=message)
signed = account.sign_message(signable)

payload = {
    "x402Version": 2,
    "scheme": "exact",
    "network": accept["network"],
    "payload": {
        "signature": signed.signature.hex(),
        "authorization": {
            "from": account.address,
            "to": accept["payTo"],
            "value": str(accept["amount"]),
            "validAfter": str(valid_after),
            "validBefore": str(valid_before),
            "nonce": nonce
        }
    }
}

payment_header = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")

# Step 4: Resubmit request with payment header
res_paid = requests.get(TARGET_URL, headers={"payment-signature": payment_header, "x-payment": payment_header})

print(f"[*] Final HTTP Status: {res_paid.status_code}")
if res_paid.status_code == 200:
    print("[+] Live Unlocked Intel Payload:")
    print(json.dumps(res_paid.json(), indent=2))
else:
    print("[-] Settlement failed:")
    print(res_paid.text)