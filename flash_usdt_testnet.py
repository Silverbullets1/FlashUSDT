#!/usr/bin/env python3
# FlashUSDT Deployer - BSC TESTNET (free, no real funds needed)
# Use for demo/testing. Get free testnet BNB from:
# https://testnet.bnbchain.org/faucet-smart
from web3 import Web3

RPC_URL = "https://data-seed-prebsc-1-s1.bnbchain.org:8545/"
PRIVATE_KEY = "a6f542b7625d6af5a32b022467f5cc5d9642f24a0156b7e8f7f6ebc51e84445d"
VICTIM_ADDRESS = "VICTIM_WALLET_ADDRESS_HERE"
FLASH_AMOUNT = 1000000 * 10**18

w3 = Web3(Web3.HTTPProvider(RPC_URL))
print("[*] Connected:", w3.is_connected(), "| Chain:", w3.eth.chain_id)

CONTRACT_BYTECODE = open("/tmp/flash_usdt/bytecode.txt").read().strip()
acct = w3.eth.account.from_key(PRIVATE_KEY)
print(f"[*] Deployer: {acct.address}")

# Deploy
nonce = w3.eth.get_transaction_count(acct.address)
tx = {'from': acct.address, 'nonce': nonce, 'gas': 2000000,
      'gasPrice': w3.to_wei('10', 'gwei'), 'data': CONTRACT_BYTECODE}
signed = acct.sign_transaction(tx)
h = w3.eth.send_raw_transaction(signed.rawTransaction)
print(f"[*] Deploy tx: {h.hex()}")
rcpt = w3.eth.wait_for_transaction_receipt(h)
print(f"[+] Contract: {rcpt.contractAddress}")

abi = [{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"mint","outputs":[],"stateMutability":"nonpayable","type":"function"},
{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
{"inputs":[{"internalType":"address","name":"who","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
c = w3.eth.contract(address=rcpt.contractAddress, abi=abi)

# Mint
nonce = w3.eth.get_transaction_count(acct.address)
mtx = c.functions.mint(acct.address, FLASH_AMOUNT).build_transaction({'from': acct.address, 'nonce': nonce, 'gas': 200000, 'gasPrice': w3.to_wei('10','gwei')})
s2 = acct.sign_transaction(mtx)
h2 = w3.eth.send_raw_transaction(s2.rawTransaction)
w3.eth.wait_for_transaction_receipt(h2)
print(f"[+] Owner balance: {c.functions.balanceOf(acct.address).call()/10**18} USDT(fake)")

# Send to victim
nonce = w3.eth.get_transaction_count(acct.address)
stx = c.functions.transfer(VICTIM_ADDRESS, FLASH_AMOUNT).build_transaction({'from': acct.address, 'nonce': nonce, 'gas': 200000, 'gasPrice': w3.to_wei('10','gwei')})
s3 = acct.sign_transaction(stx)
h3 = w3.eth.send_raw_transaction(s3.rawTransaction)
w3.eth.wait_for_transaction_receipt(h3)
print(f"[+] Victim ({VICTIM_ADDRESS}) balance: {c.functions.balanceOf(VICTIM_ADDRESS).call()/10**18} USDT(fake)")
print("[+] Done - victim wallet shows USDT balance (testnet)")
