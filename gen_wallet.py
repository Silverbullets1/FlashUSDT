#!/usr/bin/env python3
# Generate a fresh BSC wallet (address + private key)
# Use this to deploy the FlashUSDT tool. Fund it with ~0.01 BNB for gas.
from web3 import Web3
acct = Web3().eth.account.create()
print("Address:    ", acct.address)
print("Private Key:", acct.key.hex())
print("\nFund this address with ~0.01 BNB (BSC) for gas, then use in flash_usdt.py")
