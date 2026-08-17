import os
import requests
from eth_account import Account
from x402 import x402ClientSync
from x402.http.clients import wrapRequestsWithPayment
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact import register_exact_evm_client

# 1. Paste the private key corresponding to 0xe9Cc20C7139a667603BA2c3C723a82C2578dB5B9
BUYER_PRIVATE_KEY = "f1ff20aaed02e3fdc548a3640630006b1dda4786883bce86a3b1f9699425c0d3"

account = Account.from_key(BUYER_PRIVATE_KEY)
print(f"[*] Buyer Agent Address: {account.address}")

# 2. Initialize x402 Client & Register EVM Signer
client = x402ClientSync()
register_exact_evm_client(client, EthAccountSigner(account))

# 3. Create an automated payment session
session = wrapRequestsWithPayment(requests.Session(), client)

# 4. Request the intelligence endpoint
API_URL = "https://x402-intel-engine-production.up.railway.app/v1/intel/pulse/SOL"
print(f"[*] Requesting protected endpoint: {API_URL}")

response = session.get(API_URL)

print(f"[*] Final HTTP Status: {response.status_code}")
print(f"[*] Unlocked Intel Payload:\n{response.text}")