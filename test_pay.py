import os
import json
import asyncio
import httpx
from dotenv import load_dotenv
from eth_account import Account
from x402.client import x402Client
from x402.http.clients.httpx import x402HttpxClient
from x402.mechanisms.evm.exact import register_exact_evm_client

load_dotenv()

BUYER_PRIVATE_KEY = os.getenv("BUYER_PRIVATE_KEY")
TARGET_URL = "https://x402-intel-engine-production.up.railway.app/v1/intel/pulse/SOL"

async def main():
    global BUYER_PRIVATE_KEY
    if not BUYER_PRIVATE_KEY:
        print("[!] No BUYER_PRIVATE_KEY found in .env.")
        print("[*] Generating ephemeral test wallet:")
        ephemeral_acc = Account.create()
        print(f"    Address: {ephemeral_acc.address}")
        print(f"    Private Key: {ephemeral_acc.key.hex()}")
        print("[!] Fund this address with at least $0.05 USDC on Base Mainnet to settle live.")
        account = ephemeral_acc
    else:
        account = Account.from_key(BUYER_PRIVATE_KEY)
        print(f"[*] Using Buyer Address: {account.address}")

    # Initialize EVM client
    client = x402Client()
    register_exact_evm_client(client, account)

    print(f"[*] Sending paid request to: {TARGET_URL}")
    async with x402HttpxClient(client) as http:
        response = await http.get(TARGET_URL)
        print(f"[*] Response Status: {response.status_code}")
        if response.status_code == 200:
            print("[+] Payment settled successfully! Returned Intel:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"[-] Request returned: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(main())