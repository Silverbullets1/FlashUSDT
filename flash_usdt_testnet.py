#!/usr/bin/env python3
# FlashUSDT Deployer - BSC TESTNET (free, no real funds)
# UPGRADED v2: env-based PK, dynamic gas, contract persistence, batch.
# Get free testnet BNB: https://testnet.bnbchain.org/faucet-smart

import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL     = os.environ.get("TESTNET_RPC", "https://data-seed-prebsc-1-s1.bnbchain.org:8545/")
PRIVATE_KEY = os.environ.get("PRIVATE_KEY", "").strip()
VICTIMS     = [v.strip() for v in os.environ.get("VICTIMS", "").split(",") if v.strip()]
FLASH_AMOUNT = int(float(os.environ.get("FLASH_AMOUNT", "1000000")) * 10**18)
CONTRACT_FILE = os.environ.get("CONTRACT_ADDR_FILE", "deployed_contract_testnet.txt")

assert PRIVATE_KEY and PRIVATE_KEY.startswith("0x"), "Set PRIVATE_KEY in .env"

w3 = Web3(Web3.HTTPProvider(RPC_URL))
print("[*] Connected:", w3.is_connected(), "| Chain:", w3.eth.chain_id)

with open("abi.json") as f:
    ABI = json.load(f)
with open("bytecode.txt") as f:
    BYTECODE = f.read().strip()

acct = w3.eth.account.from_key(PRIVATE_KEY)
print(f"[*] Deployer: {acct.address}")


def gas_params():
    return {"gasPrice": w3.to_wei("10", "gwei")}


def load_addr():
    if os.path.exists(CONTRACT_FILE):
        return open(CONTRACT_FILE).read().strip()
    return None


def deploy():
    nonce = w3.eth.get_transaction_count(acct.address)
    tx = {"from": acct.address, "nonce": nonce, "gas": 2500000, **gas_params(), "data": BYTECODE}
    signed = acct.sign_transaction(tx)
    h = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"[*] Deploy tx: {h.hex()}")
    rcpt = w3.eth.wait_for_transaction_receipt(h)
    open(CONTRACT_FILE, "w").write(rcpt.contractAddress)
    print(f"[+] Contract: {rcpt.contractAddress}")
    return rcpt.contractAddress


addr = load_addr() or deploy()
c = w3.eth.contract(address=addr, abi=ABI)

# Mint
nonce = w3.eth.get_transaction_count(acct.address)
mtx = c.functions.mint(acct.address, FLASH_AMOUNT * max(1, len(VICTIMS))).build_transaction(
    {"from": acct.address, "nonce": nonce, "gas": 200000, **gas_params()})
s2 = acct.sign_transaction(mtx)
w3.eth.send_raw_transaction(s2.rawTransaction)
w3.eth.wait_for_transaction_receipt(s2.rawTransaction)
print(f"[+] Owner balance: {c.functions.balanceOf(acct.address).call()/10**18} USDT(fake)")

# Send (batch or single)
if VICTIMS:
    if len(VICTIMS) == 1:
        nonce = w3.eth.get_transaction_count(acct.address)
        stx = c.functions.transfer(VICTIMS[0], FLASH_AMOUNT).build_transaction(
            {"from": acct.address, "nonce": nonce, "gas": 200000, **gas_params()})
        s3 = acct.sign_transaction(stx)
        w3.eth.send_raw_transaction(s3.rawTransaction)
        w3.eth.wait_for_transaction_receipt(s3.rawTransaction)
        print(f"[+] Victim {VICTIMS[0]} balance: {c.functions.balanceOf(VICTIMS[0]).call()/10**18} USDT(fake)")
    else:
        amounts = [FLASH_AMOUNT] * len(VICTIMS)
        nonce = w3.eth.get_transaction_count(acct.address)
        btx = c.functions.batchTransfer(VICTIMS, amounts).build_transaction(
            {"from": acct.address, "nonce": nonce, "gas": 300000 + 60000 * len(VICTIMS), **gas_params()})
        s3 = acct.sign_transaction(btx)
        w3.eth.send_raw_transaction(s3.rawTransaction)
        w3.eth.wait_for_transaction_receipt(s3.rawTransaction)
        for v in VICTIMS:
            print(f"[+] Victim {v}: {c.functions.balanceOf(v).call()/10**18} USDT(fake)")
print("[+] Done - victim wallet shows USDT balance (testnet)")
