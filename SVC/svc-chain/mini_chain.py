import json
import hashlib
import time
import os
from datetime import datetime

CHAIN_FILE = "svc_chain.json"
TARGET_BLOCK_TIME = 60      # seconds
DIFFICULTY_PERIOD = 10      # adjust every 10 blocks

class MiniChain:
    def __init__(self):
        self.chain = []
        self.utxos = {}          # txid -> amount (for simplicity)
        self.load_chain()

    def load_chain(self):
        if os.path.exists(CHAIN_FILE):
            with open(CHAIN_FILE) as f:
                data = json.load(f)
                self.chain = data["chain"]
                self.utxos = data.get("utxos", {})
        else:
            self.create_genesis()

    def save_chain(self):
        with open(CHAIN_FILE, "w") as f:
            json.dump({"chain": self.chain, "utxos": self.utxos}, f, indent=2)

    def create_genesis(self):
        genesis = {
            "index": 0,
            "timestamp": int(time.time()),
            "prev_hash": "0" * 64,
            "nonce": 0,
            "difficulty": 4,
            "txs": [{"type": "genesis", "coin": "SVC genesis block"}],
            "hash": ""
        }
        genesis["hash"] = self.calculate_hash(genesis)
        self.chain.append(genesis)
        self.save_chain()
        print("✅ Genesis block created")

    def calculate_hash(self, block):
        block_str = json.dumps(block, sort_keys=True)
        return hashlib.sha256(block_str.encode()).hexdigest()

    def mine_block(self, new_txs, miner_address):
        last_block = self.chain[-1]
        difficulty = last_block["difficulty"]

        block = {
            "index": len(self.chain),
            "timestamp": int(time.time()),
            "prev_hash": last_block["hash"],
            "nonce": 0,
            "difficulty": difficulty,
            "txs": new_txs,
            "hash": ""
        }

        print(f"⛏️  Mining block {block['index']} (difficulty {difficulty})...")
        start = time.time()

        while True:
            block["nonce"] += 1
            block["hash"] = self.calculate_hash(block)
            if block["hash"].startswith("0" * difficulty):
                break

        duration = time.time() - start
        print(f"✅ Block mined in {duration:.1f}s → {block['hash'][:12]}...")

        # Add to chain
        self.chain.append(block)

        # Simple UTXO update (for demo)
        for tx in new_txs:
            if isinstance(tx, dict) and "amount" in tx:
                self.utxos[tx.get("txid", hashlib.sha256(str(tx).encode()).hexdigest())] = tx["amount"]

        self.adjust_difficulty()
        self.save_chain()
        return block

    def adjust_difficulty(self):
        if len(self.chain) % DIFFICULTY_PERIOD != 0:
            return
        # Very simple DAA for now
        last_10 = self.chain[-DIFFICULTY_PERIOD:]
        total_time = last_10[-1]["timestamp"] - last_10[0]["timestamp"]
        expected_time = DIFFICULTY_PERIOD * TARGET_BLOCK_TIME
        if total_time < expected_time // 2:
            self.chain[-1]["difficulty"] += 1
        elif total_time > expected_time * 2:
            self.chain[-1]["difficulty"] = max(1, self.chain[-1]["difficulty"] - 1)
        print(f"📊 Difficulty adjusted to {self.chain[-1]['difficulty']}")

    def get_balance(self, address):
        # Placeholder — later we will tie this to your keychain roles
        return sum(self.utxos.values()) if self.utxos else 1000

if __name__ == "__main__":
    chain = MiniChain()
    print(f"✅ Mini-chain loaded — {len(chain.chain)} blocks")
    # Quick test mine
    test_tx = [{"type": "coinbase", "amount": 50, "to": "miner-test-address"}]
    chain.mine_block(test_tx, "miner-test-address")
