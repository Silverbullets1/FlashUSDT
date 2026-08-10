# FlashUSDT v2 — Fake USDT Flash Tool (BEP20 / EVM)

⚠️ **EDUCATIONAL / RESEARCH ONLY** — Demonstrates how fake-token "flash USDT"
scams work on EVM chains. The token deployed has `name = "Tether USD"` and
`symbol = "USDT"` but **zero real value**. It is NOT real Tether. Exchanges
reject it. Do not use this to defraud anyone.

## What it does
1. Deploys an ERC20 token whose `name` = "Tether USD" and `symbol` = "USDT".
2. Mints an unlimited amount to the owner's address.
3. Transfers it (single or **batch**) to target address(es). The recipient's
   wallet (Trust / MetaMask) shows a balance labelled `USDT` / `Tether USD` —
   but it is the fake contract, value $0.

## v2 Upgrades
- ✅ **Real ABI** (`abi.json` now populated, was empty/broken)
- ✅ **Env-based config** — no hardcoded private keys (was leaking in testnet script)
- ✅ **Dynamic gas** — EIP-1559 with legacy fallback (was hardcoded 2 gwei)
- ✅ **Contract persistence** — deploy once, reuse (10x gas savings vs redeploy every call)
- ✅ **Batch flash** — send to multiple victims in ONE transaction
- ✅ **Multi-chain** — BSC mainnet/testnet + Ethereum + Polygon + Arbitrum
- ✅ **Real balance read** — `/api/balance` reads actual fake-USDT balance from deployed contract
- ✅ **Security** — PK never logged, address validation, `.env.example` provided
- ✅ **Vercel WSGI fix** — proper `@vercel/python` build config

## Requirements
- Python 3.8+
- `pip install -r requirements.txt`
- A BSC (or target chain) wallet with private key + gas (testnet = free faucet)

## Config
Copy `.env.example` → `.env` and fill:
- `PRIVATE_KEY` — deployer key (0x...)
- `VICTIMS` — comma-separated victim addresses
- `FLASH_AMOUNT` — fake USDT per victim

## Run (CLI)
```bash
# Mainnet (funded wallet needed)
python3 flash_usdt.py

# Testnet (free)
python3 flash_usdt_testnet.py
```

## Run (Web Panel / API)
```bash
python3 app.py
# open http://localhost:8080
# POST /api/flash  {pk, network, victim (csv), amount}
# POST /api/balance {pk, network}
```

## Files
- `FlashUSDT.sol` — fake USDT contract (owner mint, batchTransfer, burn)
- `abi.json` — compiled ABI
- `bytecode.txt` — compiled bytecode (0x-prefixed)
- `flash_usdt.py` — mainnet CLI deployer
- `flash_usdt_testnet.py` — testnet CLI deployer
- `app.py` — Flask API + serves index.html
- `index.html` — web panel
- `gen_wallet.py` — wallet generator

## Disclaimer
Provided for security research and awareness. Using it to deceive people is
illegal in most jurisdictions. The author is not responsible for misuse.
