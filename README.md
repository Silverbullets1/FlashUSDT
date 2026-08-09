# FlashUSDT — Fake USDT Flash Tool (BEP20/BSC)

⚠️ **EDUCATIONAL / RESEARCH ONLY** — This is a demonstration of how fake-token
"flash USDT" scams work on EVM chains. The token deployed here has the name and
symbol `USDT` but **zero real value**. It is NOT real Tether. Exchanges will reject
it. Do not use this to defraud anyone — this repo exists to show how the scam
mechanism operates so defenders can recognize it.

## What it does
1. Deploys an ERC20 token whose `name` and `symbol` are both `USDT`.
2. Mints an unlimited amount to the owner's address.
3. Transfers it to a target address. The recipient's wallet (Trust Wallet /
   MetaMask) shows a balance labelled `USDT` — but it is the fake contract, value $0.

## Requirements
- Python 3.8+
- `pip install web3`
- A BSC wallet with the private key and ~0.01 BNB for gas.

## Config (flash_usdt.py)
- `RPC_URL` — BSC mainnet RPC
- `PRIVATE_KEY` — deployer wallet key
- `OWNER_ADDRESS` — deployer address
- `VICTIM_ADDRESS` — where to send the flash USDT
- `FLASH_AMOUNT` — how much fake USDT to mint/send

## Run
```
pip install web3
python3 flash_usdt.py
```

## Files
- `FlashUSDT.sol` — the fake USDT contract
- `flash_usdt.py` — deployer + mint + send script
- `abi.json` — compiled ABI
- `bytecode.txt` — compiled bytecode

## Disclaimer
This code is provided for security research and awareness. Using it to deceive
people is illegal in most jurisdictions. The author is not responsible for misuse.
