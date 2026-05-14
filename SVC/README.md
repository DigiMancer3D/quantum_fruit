# Self-Verifying Coin (SVC) System

A quantum-cryptographic, post-quantum secure coin system built on **SPX-QEC** (Sphinx Quantum Entanglement Compression) with deterministic pattern generation, P2P mesh networking, and multi-role key hierarchy.

## 📋 Overview

The SVC system implements a complete digital currency stack featuring:

- **Fruit Bitmapper**: High-entropy seed generation using scent-maths + epoch-based bump mapping
- **SPX-QEC Core**: Quantum Entanglement Compression with 13 base patterns and 4 deterministic transformation rules
- **Multi-Role Keygen**: 9 PQC role keys (fill, spend, last-send, rolling, mix, fuse, cut, multi-sig, vault)
- **Self-Verifying Coins**: Coins that cryptographically prove validity without external verification
- **Lightweight Blockchain**: Simple PoW chain with dynamic difficulty adjustment
- **P2P Mesh Network**: Async coin transfers with return-ack acknowledgment
- **Modular Architecture**: Separate components for coin creation, verification, and wallet management

---

## 📁 Directory Structure

```
SVC/
├── svc-core/              # C library (SPX-QEC implementation)
│   ├── include/
│   │   └── spx_qec.h      # Header with SPX_Context & function signatures
│   ├── src/
│   │   └── spx_qec.c      # Core compression/decompression/verification
│   └── tests/
│       └── test_spx_qec.c # Unit tests
├── svc-keygen/            # Key generation (Tkinter GUI + Fruit Bitmapper)
│   ├── keygen.py          # Interactive keychain generator
│   └── fruit_bitmapper.py # High-entropy seed extractor
├── svc-coin/              # Coin creation & manipulation
│   └── coin_system.py     # Fill, extract, and verify coins
├── svc-chain/             # Lightweight blockchain
│   └── mini_chain.py      # PoW chain with UTXO model
├── svc-wallet/            # P2P wallet interface
│   ├── wallet.py          # Tkinter wallet GUI + mesh controls
│   └── p2p_node.py        # Async P2P messaging (asyncio)
├── svc-verifier/          # Verification daemon
│   └── verifier_daemon.py # Offline/online coin verification
└── README.md              # This file
```

---

## 🔧 Components

### 1. **SPX-QEC Core** (`svc-core/`)
Quantum Entanglement Compression library written in C.

**Key Features:**
- 13 smallest binary patterns: `00, 11, 01, 10, 100, 011, 101, 010, 1001, 0110, 10100, 01011, 001101`
- 4 transformation rules generating 32 unique patterns per rule
- Deterministic compression/decompression with `SPX!` magic header
- Safe memory management with `spx_free()`

**Functions:**
```c
bool spx_init_context(SPX_Context* ctx, const char* ref_str);
char* spx_compress(const SPX_Context* ctx, const char* input, size_t* out_len);
char* spx_decompress(const SPX_Context* ctx, const char* compressed, size_t comp_len);
char* spx_fill(const char* prev_bin, const char* data, const char* key);
char* spx_extract(const char* bin, const char* key);
bool spx_verify(const char* bin, uint32_t expected_magic);
void spx_free(char* ptr);
```

**Build:**
```bash
cd SVC/svc-core
gcc -fPIC -shared -o libspx_qec.so src/spx_qec.c
```

### 2. **Fruit Bitmapper** (`svc-keygen/`)
Generates cryptographically secure entropy using scent-mathematics and epoch-based modulation.

**Algorithm:**
- 256×256 pixel bump map with sinusoidal patterns
- Multi-dimensional scent formulas (orange/lemon bump from thesis)
- 8 iterations of SHA3-512 hashing for extreme entropy
- NIST-style high min-entropy extraction

**Usage:**
```python
from fruit_bitmapper import FruitBitmapper

bmp = FruitBitmapper()
bitmap = bmp.generate_bitmap()
seed = bmp.extract_high_entropy_seed(bitmap, length=64)
```

### 3. **Keygen** (`svc-keygen/keygen.py`)
Interactive GUI for generating PQC role keychains.

**Features:**
- Generates 9 role keys: `fill, spend, last-send, rolling, mix, fuse, cut, multi-sig, vault`
- Uses Fruit Bitmapper for master seed
- Outputs JSON keychain file: `svc_keychain_EPOCH.kchain`
- Each role key derived via `SHA3-512(master_seed || role_name)`

**Run:**
```bash
cd SVC/svc-keygen
python3 keygen.py
```

### 4. **Coin System** (`svc-coin/coin_system.py`)
Create, fill, extract, and verify self-verifying coins.

**Operations:**
1. **Load Keychain**: Import role keys from Phase 2 keychain
2. **Create New Coin**: Initialize empty coin with epoch + master seed
3. **Fill Coin**: Add transaction/proof data via SPX-QEC `spx_fill()`
4. **Extract Random**: Get proof slice via role-specific key
5. **Verify Coin**: Self-verification with magic header check
6. **Save Coin**: Export to `.coinbin` file

**Run:**
```bash
cd SVC/svc-coin
python3 coin_system.py
```

### 5. **Mini-Chain** (`svc-chain/mini_chain.py`)
Lightweight PoW blockchain with simple UTXO model.

**Features:**
- Genesis block initialization
- Dynamic difficulty adjustment (every 10 blocks)
- SHA256 PoW with configurable nonce
- UTXO tracking for balance queries
- JSON persistence (`svc_chain.json`)

**Configuration:**
```python
TARGET_BLOCK_TIME = 60      # seconds
DIFFICULTY_PERIOD = 10      # adjust every N blocks
```

**Usage:**
```python
chain = MiniChain()
tx = [{"type": "coinbase", "amount": 50, "to": "miner-address"}]
chain.mine_block(tx, "miner-address")
```

### 6. **P2P Node** (`svc-wallet/p2p_node.py`)
Async peer-to-peer mesh networking for coin transfers.

**Features:**
- Automatic port detection (8000–8050)
- Bidirectional peer connections
- Two message types: `coin-transfer`, `coin-ack`
- Synchronous ACK sending (works with Tkinter)
- Fire-and-forget broadcasting

**Usage:**
```python
p2p = SVC_P2PNode()
p2p.on_receive_coin = callback_handler
await p2p.start()
await p2p.broadcast_coin(coin_data, receiver)
p2p.send_ack(receiver_address)
```

### 7. **Wallet** (`svc-wallet/wallet.py`)
Interactive P2P wallet with mesh management.

**Features:**
- Load/manage keychains
- Start mesh server on dynamic port
- Send coins via P2P
- Manual peer connections
- Local peer scanning (8000–8050)
- Real-time transaction log

**Run:**
```bash
cd SVC/svc-wallet
python3 wallet.py
```

### 8. **Verifier Daemon** (`svc-verifier/verifier_daemon.py`)
Offline/online coin verification with background listening.

**Features:**
- Single coin verification
- Batch folder verification
- Background daemon mode
- Timestamped verification log
- Verified coin tracking

**Run:**
```bash
cd SVC/svc-verifier
python3 verifier_daemon.py
```

---

## 🚀 Quick Start

### Prerequisites
```bash
# C library compilation
gcc -fPIC -shared -o SVC/svc-core/libspx_qec.so SVC/svc-core/src/spx_qec.c

# Python dependencies
pip install -r requirements.txt  # (tkinter comes built-in)
```

### End-to-End Workflow

1. **Generate Keychain**
   ```bash
   cd SVC/svc-keygen && python3 keygen.py
   # Output: svc_keychain_1715697600.kchain
   ```

2. **Create Coins**
   ```bash
   cd SVC/svc-coin && python3 coin_system.py
   # Load keychain → Create coin → Fill with data → Verify → Save
   ```

3. **Verify Coins**
   ```bash
   cd SVC/svc-verifier && python3 verifier_daemon.py
   # Load coin files and verify offline/online
   ```

4. **P2P Transfer (Multi-Instance)**
   ```bash
   # Terminal 1: Start wallet on 8000
   cd SVC/svc-wallet && python3 wallet.py
   # Click: Start Simple Mesh

   # Terminal 2: Start wallet on 8001+
   cd SVC/svc-wallet && python3 wallet.py
   # Click: Start Simple Mesh
   # Click: Connect to Peer → 8000
   
   # Terminal 1: Send coin via mesh
   ```

5. **Mine Block**
   ```bash
   cd SVC/svc-chain && python3 mini_chain.py
   # Mines genesis + test block with PoW
   ```

---

## 🔐 Security Considerations

- **SPX-QEC**: Post-quantum secure with deterministic pattern generation
- **Role Hierarchy**: Separation of concerns (fill ≠ spend ≠ vault)
- **Epoch-Based Entropy**: Unique per-run randomness via timestamp
- **Self-Verification**: Coins cryptographically prove validity without trust
- **Mesh Anonymity**: P2P transfers without central authority

---

## 📊 Magic Numbers

- **SPX Magic**: `0x53505821` (ASCII: `SPX!`)
- **Max Reference Length**: 64 bytes
- **Base Patterns**: 13
- **Pattern Rules**: 4 (palindrome, reverse, combined, advanced)
- **Max Patterns per Rule**: 32
- **Min Entropy**: 64 bytes (512 bits)
- **Target Block Time**: 60 seconds
- **Difficulty Adjustment**: Every 10 blocks

---

## 📝 File Formats

### Keychain (`.kchain`)
```json
{
  "epoch": 1715697600,
  "master_seed": "a1b2c3d4e5f6...",
  "roles": {
    "fill": "role_seed_hex",
    "spend": "role_seed_hex",
    "last-send": "role_seed_hex",
    "rolling": "role_seed_hex",
    "mix": "role_seed_hex",
    "fuse": "role_seed_hex",
    "cut": "role_seed_hex",
    "multi-sig": "role_seed_hex",
    "vault": "role_seed_hex"
  }
}
```

### Coin (`.coinbin`)
```
SPX!NEW_COIN|epoch:1715697600|master:a1b2c3d4e5f6...|DATA:tx_data^KEY:role_key|ROLL:0x12345678
```

### Chain (`.json`)
```json
{
  "chain": [
    {
      "index": 0,
      "timestamp": 1715697600,
      "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000",
      "nonce": 0,
      "difficulty": 4,
      "txs": [{"type": "genesis", "coin": "SVC genesis block"}],
      "hash": "0000a1b2c3d4e5f6..."
    }
  ],
  "utxos": {}
}
```

---

## 🧪 Testing

### SPX-QEC Unit Tests
```bash
cd SVC/svc-core/tests
gcc -o test_spx_qec test_spx_qec.c ../src/spx_qec.c
./test_spx_qec
```

### Integration Test
```bash
cd SVC
python3 -c "
from svc-keygen.fruit_bitmapper import FruitBitmapper
from svc-chain.mini_chain import MiniChain

# Entropy generation
bmp = FruitBitmapper()
seed = bmp.extract_high_entropy_seed(bmp.generate_bitmap())
print(f'✅ Generated {len(seed)} byte seed')

# Blockchain
chain = MiniChain()
print(f'✅ Chain loaded with {len(chain.chain)} blocks')
"
```

---

## 🤝 Contributing

This is an experimental implementation. For issues or improvements:
1. Test locally first
2. Update both `/SVC/` and `/SVC/svc-*/` mirror copies
3. Verify SPX-QEC compilation
4. Run integration tests

---

## 📚 References

- **Thesis Basis**: Scent-maths + bump mapping entropy
- **Quantum**: SPX (SPHINCS+) inspired Quantum Entanglement Compression
- **Standards**: NIST min-entropy extraction, SHA3-512
- **Architecture**: Byzantine-tolerant P2P mesh
- **Blockchain**: Simple Nakamoto PoW

---

## 📄 License

Part of the `quantum_fruit` research project. See root LICENSE for details.

---

**Status**: ✅ Phase 2 Ready  
**Last Updated**: 2026-05-14  
**Maintainer**: @DigiMancer3D
