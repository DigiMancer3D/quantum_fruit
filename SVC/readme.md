# Install
cd ~/svc
python3 -m venv venv
source venv/bin/activate
pip install libp2p


# Terminal 1 - Verifier Daemon (always running)
cd ~/svc/svc-verifier
python3 verifier_daemon.py

# Terminal 2 - Wallet
cd ~/svc/svc-wallet
python3 wallet.py

# Terminal 3 - Mini-Chain
cd ~/svc/svc-chain
python3 mini_chain.py
